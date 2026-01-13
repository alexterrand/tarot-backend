"""Game logger service - wraps game logic with Supabase logging.

This service acts as a middleware between the API and game logic,
capturing game data for Supabase without polluting the game service.
"""

import logging
from typing import Any
from uuid import UUID

from tarot_logic.card import Card
from tarot_logic.game_state import GameState

from app.services.card_serializer import card_to_str, cards_to_list
from app.services.game_logger import game_logger

logger = logging.getLogger(__name__)


class GameLogData:
    """In-memory cache for game data before batch logging."""

    def __init__(self, game_id: UUID, game_round_id: UUID):
        self.game_id = game_id
        self.game_round_id = game_round_id

        # Cache for tricks and decisions
        self.tricks: list[dict[str, Any]] = []
        self.bot_decisions: list[dict[str, Any]] = []

        # Track current trick number
        self.current_trick_number = 0


class GameLoggerService:
    """Service that wraps game logic with Supabase logging."""

    def __init__(self):
        """Initialize logger service with in-memory cache."""
        self.log_data: dict[str, GameLogData] = {}  # game_id -> GameLogData

    def start_game_logging(
        self,
        game_id: str,
        game_state: GameState,
        initial_hands: dict[str, list[Card]],
    ) -> None:
        """Start logging for a new game.

        Args:
            game_id: Game ID from GameService
            game_state: Current game state
            initial_hands: Dict mapping player_id to initial hand (before any plays)
        """
        try:
            # Create game entry in Supabase
            player_ids = [p.player_id for p in game_state.players]
            num_players = len(player_ids)

            supabase_game_id = game_logger.create_game(
                player_ids=player_ids,
                num_players=num_players,
            )

            # Create game round (placeholder contract since no bidding yet)
            # Use first player as "taker" for now
            taker_id = player_ids[0]

            # Serialize hands
            serialized_hands = {
                player_id: cards_to_list(hand)
                for player_id, hand in initial_hands.items()
            }

            # Calculate hand strengths
            hand_strengths = {
                player_id: sum(card.get_points() for card in hand)
                for player_id, hand in initial_hands.items()
            }

            # Serialize dog
            dog_serialized = cards_to_list(game_state.dog)

            # Create round (default contract "petite" with 51 points needed)
            game_round_id = game_logger.create_game_round(
                game_id=supabase_game_id,
                round_number=1,
                taker_id=taker_id,
                contract_type="petite",  # Default for V1 (no bidding)
                dog_cards=dog_serialized,
                initial_hands=serialized_hands,
                hand_strengths=hand_strengths,
                contract_points_needed=51,  # Default with 2 oudlers
            )

            # Initialize log cache
            self.log_data[game_id] = GameLogData(supabase_game_id, game_round_id)

            logger.info(
                f"Game logging started: {game_id} -> Supabase {supabase_game_id}"
            )

        except Exception as e:
            logger.warning(f"Failed to start game logging: {e}")
            # Don't raise - game should continue even if logging fails

    def log_card_played(
        self,
        game_id: str,
        player_id: str,
        card: Card,
        hand_before: list[Card],
        legal_moves: list[Card],
        trick_state_before: list[Card],
        position_in_trick: int,
        strategy_name: str = "human",
    ) -> None:
        """Log a card play decision (cached, not written to DB yet).

        Args:
            game_id: Game ID
            player_id: Player who played
            card: Card played
            hand_before: Player's hand before playing
            legal_moves: Legal moves available
            trick_state_before: Cards in trick before this play
            position_in_trick: Position (0-3) when playing
            strategy_name: Bot strategy name ("bot-naive", "bot-random", "human")
        """
        log_data = self.log_data.get(game_id)
        if not log_data:
            logger.warning(f"No log data for game {game_id}")
            return

        try:
            # Serialize cards
            card_str = card_to_str(card)
            hand_before_str = cards_to_list(hand_before)
            legal_moves_str = cards_to_list(legal_moves)
            trick_state_str = [
                {"card": card_to_str(c), "position": i}
                for i, c in enumerate(trick_state_before)
            ]

            # Cache decision
            decision = {
                "trick_number": log_data.current_trick_number + 1,  # 1-indexed
                "player_id": player_id,
                "strategy_name": strategy_name,
                "hand_before": hand_before_str,
                "legal_moves": legal_moves_str,
                "trick_state_before": trick_state_str,
                "position_in_trick": position_in_trick,
                "card_played": card_str,
                "is_taker": False,  # TODO: Update when bidding is implemented
                "contract_type": "petite",  # Default for V1
            }

            log_data.bot_decisions.append(decision)

        except Exception as e:
            logger.warning(f"Failed to log card play: {e}")

    def log_trick_completed(
        self,
        game_id: str,
        trick_cards: list[Card],
        trick_player_indices: list[int],
        winner_player_id: str,
        game_state: GameState,
    ) -> None:
        """Log a completed trick (cached, not written to DB yet).

        Args:
            game_id: Game ID
            trick_cards: Cards played in this trick
            trick_player_indices: Player indices who played each card
            winner_player_id: Player who won the trick
            game_state: Current game state
        """
        log_data = self.log_data.get(game_id)
        if not log_data:
            logger.warning(f"No log data for game {game_id}")
            return

        try:
            # Increment trick number
            log_data.current_trick_number += 1

            # Serialize trick data
            cards_played = [
                {
                    "player": game_state.players[player_idx].player_id,
                    "card": card_to_str(card),
                    "position": pos,
                }
                for pos, (card, player_idx) in enumerate(
                    zip(trick_cards, trick_player_indices)
                )
            ]

            # Calculate trick points
            trick_points = sum(card.get_points() for card in trick_cards)

            # Cache trick
            trick = {
                "trick_number": log_data.current_trick_number,
                "cards_played": cards_played,
                "winner_player_id": winner_player_id,
                "trick_points": trick_points,
            }

            log_data.tricks.append(trick)

        except Exception as e:
            logger.warning(f"Failed to log trick: {e}")

    def end_game_logging(
        self,
        game_id: str,
        game_state: GameState,
    ) -> None:
        """End game logging - batch write all cached data to Supabase.

        Args:
            game_id: Game ID
            game_state: Final game state
        """
        log_data = self.log_data.get(game_id)
        if not log_data:
            logger.warning(f"No log data for game {game_id}")
            return

        try:
            # Calculate final scores (simplified for V1 - no contract logic)
            # In V1, just count points won by each player
            player_points = {
                player.player_id: sum(
                    card.get_points()
                    for trick in player.tricks_won
                    for card in trick
                )
                for player in game_state.players
            }

            # For V1 (no taker), use placeholder values
            taker_team_points = 45.5  # Placeholder
            defense_team_points = 45.5  # Placeholder
            contract_won = True  # Placeholder

            # Batch log all tricks and decisions
            game_logger.batch_log_round(
                game_round_id=log_data.game_round_id,
                tricks=log_data.tricks,
                bot_decisions=log_data.bot_decisions,
            )

            # Update round results
            game_logger.update_round_results(
                game_round_id=log_data.game_round_id,
                taker_team_points=taker_team_points,
                defense_team_points=defense_team_points,
                contract_won=contract_won,
            )

            # Update game leaderboard (placeholder for V1)
            leaderboard = {pid: int(pts) for pid, pts in player_points.items()}
            game_logger.update_game_leaderboard(
                game_id=log_data.game_id,
                leaderboard=leaderboard,
            )

            logger.info(
                f"Game logging completed: {game_id} "
                f"({len(log_data.tricks)} tricks, "
                f"{len(log_data.bot_decisions)} decisions)"
            )

            # Clean up cache
            del self.log_data[game_id]

        except Exception as e:
            logger.warning(f"Failed to end game logging: {e}")
            # Clean up cache even if logging failed
            if game_id in self.log_data:
                del self.log_data[game_id]


# Singleton instance
game_logger_service = GameLoggerService()
