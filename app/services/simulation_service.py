"""Service for running AI-vs-AI game simulations."""

import random
from collections import defaultdict

from tarot_logic.rules import get_legal_moves

from app.services.game_service import GameService
from app.models.simulation import SimulationConfig, GameResult, SimulationResults


class SimulationService:
    """Service to orchestrate multiple games for benchmarking and data collection."""

    def __init__(self):
        """Initialize the simulation service with a GameService instance."""
        self.game_service = GameService()

    def run_simulation(
        self, num_games: int, player_strategies: dict[str, str], seed: int | None = None
    ) -> SimulationResults:
        """
        Run a batch of AI-vs-AI games with configured strategies.

        Args:
            num_games: Number of games to simulate
            player_strategies: Mapping of player IDs to strategy names
            seed: Optional random seed for reproducibility

        Returns:
            Aggregated results from all simulated games

        Raises:
            ValueError: If player_strategies is invalid or contains unknown strategies
        """
        # Set seed if provided for reproducibility
        if seed is not None:
            random.seed(seed)

        # Validate strategies
        from tarot_logic.bots import create_strategy

        for player_id, strategy_name in player_strategies.items():
            try:
                create_strategy(strategy_name)
            except ValueError as e:
                raise ValueError(
                    f"Invalid strategy '{strategy_name}' for player '{player_id}': {e}"
                )

        # Run all games
        game_results = []
        print(f"\n=== Starting simulation: {num_games} games ===")
        print(f"Strategies: {player_strategies}\n")

        for game_num in range(1, num_games + 1):
            print(f"[Game {game_num}/{num_games}] Starting...")
            try:
                result = self._play_single_game(game_num, player_strategies)
                game_results.append(result)
                print(
                    f"[Game {game_num}/{num_games}] Complete - Winner: {result.winner_player_id}"
                )
            except Exception as e:
                print(f"[Game {game_num}/{num_games}] ERROR: {e}")
                # Continue with next game even if one fails

        # Aggregate results
        return self._aggregate_results(game_results, player_strategies)

    def _play_single_game(
        self, game_number: int, player_strategies: dict[str, str]
    ) -> GameResult:
        """
        Play a single simulated game to completion.

        Args:
            game_number: Sequential game number for tracking
            player_strategies: Mapping of player IDs to strategy names

        Returns:
            Result of the completed game
        """
        num_players = len(player_strategies)

        # Create game with no human player (all AI)
        # We'll use a dummy human player ID that doesn't exist
        game_id = self.game_service.create_game(
            num_players=num_players,
            human_player_id="__no_human__",  # Dummy ID that won't match any player
            bot_strategies=player_strategies,
        )

        # Get initial game state
        game_state_obj = self.game_service.games[game_id]

        # Play until game is over
        max_tricks = 78 // num_players  # Maximum possible tricks
        tricks_played = 0

        while not game_state_obj.is_game_over() and tricks_played < max_tricks:
            current_player = game_state_obj.get_current_player()

            # Get legal moves
            legal_moves = get_legal_moves(
                current_player.hand, game_state_obj.current_trick
            )

            if not legal_moves:
                print(f"No legal moves for {current_player.player_id}, game may be stuck")
                break

            # Get strategy and play card
            strategy_name = player_strategies[current_player.player_id]
            from tarot_logic.bots import create_strategy
            from tarot_logic.trick import Trick

            strategy = create_strategy(strategy_name)

            # Convert current_trick list to Trick object for bot strategies
            trick_obj = Trick()
            for i, card_in_trick in enumerate(game_state_obj.current_trick):
                # We need player indices, but current_trick only has cards
                # Use trick_player_indices if available
                if i < len(game_state_obj.trick_player_indices):
                    player_idx = game_state_obj.trick_player_indices[i]
                else:
                    player_idx = i  # Fallback
                trick_obj.add_card(card_in_trick, player_idx)

            card = strategy.choose_card(current_player.hand, legal_moves, trick_obj)

            # Log card play (for Supabase)
            from app.services.game_logger_service import game_logger_service

            hand_before = list(current_player.hand)
            trick_state_before = list(game_state_obj.current_trick)
            position_in_trick = len(trick_state_before)

            game_logger_service.log_card_played(
                game_id=game_id,
                player_id=current_player.player_id,
                card=card,
                hand_before=hand_before,
                legal_moves=legal_moves,
                trick_state_before=trick_state_before,
                position_in_trick=position_in_trick,
                strategy_name=strategy_name,
            )

            # Capture trick state before playing
            old_trick_size = len(game_state_obj.current_trick)
            trick_cards_before = list(game_state_obj.current_trick)
            trick_player_indices_before = list(game_state_obj.trick_player_indices)
            current_player_index = game_state_obj.current_player_index

            # Play the card
            game_state_obj.play_card(game_state_obj.current_player_index, card)
            new_trick_size = len(game_state_obj.current_trick)

            # Check if trick completed
            if new_trick_size == 0 and old_trick_size > 0:
                tricks_played += 1

                # Log trick completion
                full_trick_cards = trick_cards_before + [card]
                full_trick_indices = trick_player_indices_before + [current_player_index]
                winner_id = game_state_obj.get_current_player().player_id

                game_logger_service.log_trick_completed(
                    game_id=game_id,
                    trick_cards=full_trick_cards,
                    trick_player_indices=full_trick_indices,
                    winner_player_id=winner_id,
                    game_state=game_state_obj,
                )

        # Game over - calculate results
        # V0.5: Count tricks won (not full Tarot scoring yet - requires bidding system)
        # This is still useful for comparing bot strategies and testing Supabase logging
        scores = {
            player.player_id: len(player.tricks_won)
            for player in game_state_obj.players
        }

        # Winner is player with most tricks (temporary metric until bidding is implemented)
        if scores:
            winner_id = max(scores, key=scores.get)
        else:
            # Fallback if no tricks were won (shouldn't happen)
            winner_id = list(player_strategies.keys())[0]

        # End game logging (batch write to Supabase)
        from app.services.game_logger_service import game_logger_service

        game_logger_service.end_game_logging(
            game_id=game_id, game_state=game_state_obj
        )

        return GameResult(
            game_id=game_id,
            game_number=game_number,
            winner_player_id=winner_id,
            final_scores=scores,
            total_tricks=tricks_played,
        )

    def _aggregate_results(
        self, game_results: list[GameResult], player_strategies: dict[str, str]
    ) -> SimulationResults:
        """
        Aggregate results from multiple games.

        Args:
            game_results: List of individual game results
            player_strategies: Mapping of player IDs to strategy names

        Returns:
            Aggregated simulation statistics
        """
        total_games = len(game_results)

        # Count wins per player
        win_counts = defaultdict(int)
        score_totals = defaultdict(int)
        score_counts = defaultdict(int)

        for result in game_results:
            win_counts[result.winner_player_id] += 1

            for player_id, score in result.final_scores.items():
                score_totals[player_id] += score
                score_counts[player_id] += 1

        # Calculate win rates
        win_rates = {
            player_id: count / total_games if total_games > 0 else 0.0
            for player_id, count in win_counts.items()
        }

        # Ensure all players have entries (even if they never won)
        for player_id in player_strategies.keys():
            if player_id not in win_rates:
                win_rates[player_id] = 0.0
            if player_id not in win_counts:
                win_counts[player_id] = 0

        # Calculate average scores
        avg_scores = {
            player_id: score_totals[player_id] / score_counts[player_id]
            if score_counts[player_id] > 0
            else 0.0
            for player_id in player_strategies.keys()
        }

        return SimulationResults(
            total_games=total_games,
            player_strategies=player_strategies,
            win_counts=dict(win_counts),
            win_rates=win_rates,
            avg_scores=avg_scores,
            games_logged_to_supabase=total_games,
        )
