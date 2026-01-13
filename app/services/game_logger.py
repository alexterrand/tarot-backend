"""Game logging service for Supabase data persistence.

This service handles batch logging of game data to Supabase at the end of each round,
minimizing database writes and improving performance.
"""

import logging
from typing import Any
from uuid import UUID

from app.services.supabase_client import supabase

logger = logging.getLogger(__name__)


class GameLogger:
    """Service for logging game data to Supabase with batch operations."""

    def create_game(
        self,
        player_ids: list[str],
        num_players: int,
        game_mode: str = "standard",
    ) -> UUID:
        """Create a new game entry.

        Args:
            player_ids: List of player IDs (e.g., ["IA1", "IA2", "IA3", "IA4"])
            num_players: Number of players (3, 4, or 5)
            game_mode: Game mode (default: "standard")

        Returns:
            UUID of the created game

        Raises:
            Exception: If database insert fails
        """
        try:
            data = {
                "player_ids": player_ids,
                "num_players": num_players,
                "leaderboard": {player_id: 0 for player_id in player_ids},
                "game_mode": game_mode,
            }

            result = supabase.table("games").insert(data).execute()

            if not result.data:
                raise Exception("Failed to create game: no data returned")

            game_id = result.data[0]["id"]
            logger.info(f"Game created: {game_id}")
            return UUID(game_id)

        except Exception as e:
            logger.error(f"Failed to create game: {e}")
            raise

    def create_game_round(
        self,
        game_id: UUID,
        round_number: int,
        taker_id: str,
        contract_type: str,
        dog_cards: list[str],
        initial_hands: dict[str, list[str]],
        hand_strengths: dict[str, float],
        contract_points_needed: int,
        called_player_id: str | None = None,
    ) -> UUID:
        """Create a new game round entry.

        Args:
            game_id: Parent game UUID
            round_number: Round number (1, 2, 3...)
            taker_id: Player who took the contract
            contract_type: "petite", "garde", "garde_sans", "garde_contre"
            dog_cards: List of cards in dog (serialized)
            initial_hands: Dict mapping player_id to list of cards (serialized)
            hand_strengths: Dict mapping player_id to hand point value
            contract_points_needed: Points needed to win (36, 41, 51, 56)
            called_player_id: Player called by taker (5-player variant, optional)

        Returns:
            UUID of the created game round

        Raises:
            Exception: If database insert fails
        """
        try:
            data = {
                "game_id": str(game_id),
                "round_number": round_number,
                "taker_id": taker_id,
                "contract_type": contract_type,
                "called_player_id": called_player_id,
                "dog_cards": dog_cards,
                "initial_hands": initial_hands,
                "hand_strengths": hand_strengths,
                "contract_points_needed": contract_points_needed,
                # Placeholder values (will be updated at round end)
                "taker_team_points": 0.0,
                "defense_team_points": 0.0,
                "contract_won": False,
            }

            result = supabase.table("game_rounds").insert(data).execute()

            if not result.data:
                raise Exception("Failed to create game round: no data returned")

            game_round_id = result.data[0]["id"]
            logger.info(f"Game round created: {game_round_id} for game {game_id}")
            return UUID(game_round_id)

        except Exception as e:
            logger.error(f"Failed to create game round: {e}")
            raise

    def batch_log_round(
        self,
        game_round_id: UUID,
        tricks: list[dict[str, Any]],
        bot_decisions: list[dict[str, Any]],
    ) -> None:
        """Batch insert tricks and bot decisions for a complete round.

        This method performs efficient batch inserts to minimize database writes.

        Args:
            game_round_id: Parent game round UUID
            tricks: List of trick data dicts with keys:
                - trick_number: int
                - cards_played: list[dict] with "player", "card", "position"
                - winner_player_id: str
                - trick_points: float
            bot_decisions: List of bot decision data dicts with keys:
                - trick_id: UUID (must match inserted tricks)
                - player_id: str
                - strategy_name: str
                - hand_before: list[str]
                - legal_moves: list[str]
                - trick_state_before: list[dict]
                - position_in_trick: int
                - card_played: str
                - is_taker: bool
                - contract_type: str

        Raises:
            Exception: If batch insert fails
        """
        try:
            # Step 1: Batch insert tricks
            tricks_data = [
                {
                    "game_round_id": str(game_round_id),
                    "trick_number": trick["trick_number"],
                    "cards_played": trick["cards_played"],
                    "winner_player_id": trick["winner_player_id"],
                    "trick_points": trick["trick_points"],
                }
                for trick in tricks
            ]

            tricks_result = supabase.table("tricks").insert(tricks_data).execute()

            if not tricks_result.data:
                raise Exception("Failed to insert tricks: no data returned")

            # Map trick_number to trick_id for bot_decisions
            trick_id_map = {
                trick["trick_number"]: trick["id"]
                for trick in tricks_result.data
            }

            # Step 2: Batch insert bot decisions
            # Group decisions by trick_number to map to correct trick_id
            decisions_data = []
            for decision in bot_decisions:
                trick_number = decision["trick_number"]
                trick_id = trick_id_map.get(trick_number)

                if not trick_id:
                    logger.warning(
                        f"Skipping decision: trick_number {trick_number} not found"
                    )
                    continue

                decisions_data.append(
                    {
                        "trick_id": trick_id,
                        "player_id": decision["player_id"],
                        "strategy_name": decision["strategy_name"],
                        "hand_before": decision["hand_before"],
                        "legal_moves": decision["legal_moves"],
                        "trick_state_before": decision["trick_state_before"],
                        "position_in_trick": decision["position_in_trick"],
                        "card_played": decision["card_played"],
                        "is_taker": decision["is_taker"],
                        "contract_type": decision["contract_type"],
                    }
                )

            if decisions_data:
                supabase.table("bot_decisions").insert(decisions_data).execute()

            logger.info(
                f"Batch logged {len(tricks_data)} tricks and "
                f"{len(decisions_data)} decisions for round {game_round_id}"
            )

        except Exception as e:
            logger.warning(f"Failed to batch log round data: {e}")
            # Don't raise - game should continue even if logging fails

    def update_round_results(
        self,
        game_round_id: UUID,
        taker_team_points: float,
        defense_team_points: float,
        contract_won: bool,
    ) -> None:
        """Update game round with final results.

        Args:
            game_round_id: Game round UUID
            taker_team_points: Final points for taker team
            defense_team_points: Final points for defense team
            contract_won: Whether taker won the contract

        Raises:
            Exception: If database update fails
        """
        try:
            data = {
                "taker_team_points": taker_team_points,
                "defense_team_points": defense_team_points,
                "contract_won": contract_won,
            }

            supabase.table("game_rounds").update(data).eq(
                "id", str(game_round_id)
            ).execute()

            logger.info(f"Round results updated: {game_round_id}")

        except Exception as e:
            logger.warning(f"Failed to update round results: {e}")

    def update_game_leaderboard(
        self,
        game_id: UUID,
        leaderboard: dict[str, int],
    ) -> None:
        """Update game leaderboard with cumulative scores.

        Args:
            game_id: Game UUID
            leaderboard: Dict mapping player_id to total score

        Raises:
            Exception: If database update fails
        """
        try:
            data = {"leaderboard": leaderboard}

            supabase.table("games").update(data).eq("id", str(game_id)).execute()

            logger.info(f"Game leaderboard updated: {game_id}")

        except Exception as e:
            logger.warning(f"Failed to update game leaderboard: {e}")


# Singleton instance
game_logger = GameLogger()
