"""Tests for simulation service."""

import pytest

from app.services.simulation_service import SimulationService
from app.models.simulation import GameResult, SimulationResults


class TestSimulationService:
    """Test suite for SimulationService."""

    def test_simulation_service_init(self):
        """Test that SimulationService initializes correctly."""
        service = SimulationService()
        assert service.game_service is not None

    def test_run_simulation_single_game(self):
        """Test running a single game simulation."""
        service = SimulationService()

        player_strategies = {
            "player_1": "bot-random",
            "player_2": "bot-random",
            "player_3": "bot-random",
            "player_4": "bot-random",
        }

        results = service.run_simulation(
            num_games=1, player_strategies=player_strategies, seed=42
        )

        assert results.total_games == 1
        assert results.player_strategies == player_strategies
        assert sum(results.win_counts.values()) == 1
        assert len(results.win_rates) == 4
        assert len(results.avg_scores) == 4
        assert results.games_logged_to_supabase == 1

    def test_run_simulation_multiple_games(self):
        """Test running multiple games simulation."""
        service = SimulationService()

        player_strategies = {
            "player_1": "bot-naive",
            "player_2": "bot-random",
            "player_3": "bot-naive",
            "player_4": "bot-random",
        }

        results = service.run_simulation(
            num_games=5, player_strategies=player_strategies, seed=42
        )

        assert results.total_games == 5
        assert sum(results.win_counts.values()) == 5
        assert all(0.0 <= rate <= 1.0 for rate in results.win_rates.values())
        assert results.games_logged_to_supabase == 5

    def test_run_simulation_invalid_strategy(self):
        """Test that invalid strategy names raise ValueError."""
        service = SimulationService()

        player_strategies = {
            "player_1": "invalid-strategy",
            "player_2": "bot-random",
            "player_3": "bot-random",
            "player_4": "bot-random",
        }

        with pytest.raises(ValueError, match="Invalid strategy"):
            service.run_simulation(
                num_games=1, player_strategies=player_strategies
            )

    def test_aggregate_results_basic(self):
        """Test result aggregation with simple data."""
        service = SimulationService()

        player_strategies = {
            "player_1": "bot-naive",
            "player_2": "bot-random",
            "player_3": "bot-naive",
            "player_4": "bot-random",
        }

        game_results = [
            GameResult(
                game_id="game1",
                game_number=1,
                winner_player_id="player_1",
                final_scores={
                    "player_1": 100,
                    "player_2": 50,
                    "player_3": 80,
                    "player_4": 40,
                },
                total_tricks=8,
            ),
            GameResult(
                game_id="game2",
                game_number=2,
                winner_player_id="player_1",
                final_scores={
                    "player_1": 120,
                    "player_2": 30,
                    "player_3": 60,
                    "player_4": 50,
                },
                total_tricks=8,
            ),
        ]

        results = service._aggregate_results(game_results, player_strategies)

        assert results.total_games == 2
        assert results.win_counts["player_1"] == 2
        assert results.win_rates["player_1"] == 1.0
        assert results.avg_scores["player_1"] == 110.0
        assert results.avg_scores["player_2"] == 40.0

    def test_aggregate_results_ties_impossible(self):
        """Test that all players have win rate entries even if they didn't win."""
        service = SimulationService()

        player_strategies = {
            "player_1": "bot-naive",
            "player_2": "bot-random",
            "player_3": "bot-naive",
            "player_4": "bot-random",
        }

        game_results = [
            GameResult(
                game_id="game1",
                game_number=1,
                winner_player_id="player_1",
                final_scores={
                    "player_1": 100,
                    "player_2": 50,
                    "player_3": 80,
                    "player_4": 40,
                },
                total_tricks=8,
            ),
        ]

        results = service._aggregate_results(game_results, player_strategies)

        # All players should have entries
        assert len(results.win_rates) == 4
        assert results.win_rates["player_1"] == 1.0
        assert results.win_rates["player_2"] == 0.0
        assert results.win_rates["player_3"] == 0.0
        assert results.win_rates["player_4"] == 0.0

    def test_simulation_with_seed_reproducibility(self):
        """Test that using the same seed produces consistent results."""
        service1 = SimulationService()
        service2 = SimulationService()

        player_strategies = {
            "player_1": "bot-random",
            "player_2": "bot-random",
            "player_3": "bot-random",
            "player_4": "bot-random",
        }

        results1 = service1.run_simulation(
            num_games=3, player_strategies=player_strategies, seed=123
        )
        results2 = service2.run_simulation(
            num_games=3, player_strategies=player_strategies, seed=123
        )

        # With same seed, results should be identical
        assert results1.win_counts == results2.win_counts
        assert results1.avg_scores == results2.avg_scores


class TestSimulationIntegration:
    """Integration tests for full simulation flow."""

    def test_full_simulation_naive_vs_random(self):
        """
        Integration test: Run a small simulation with naive vs random bots.
        Naive should have higher win rate than random.
        """
        service = SimulationService()

        player_strategies = {
            "player_1": "bot-naive",
            "player_2": "bot-random",
            "player_3": "bot-naive",
            "player_4": "bot-random",
        }

        # Run 10 games (enough to see a trend, not too slow for tests)
        results = service.run_simulation(
            num_games=10, player_strategies=player_strategies, seed=42
        )

        assert results.total_games == 10
        assert results.games_logged_to_supabase == 10

        # Naive players should collectively win more than random players
        naive_wins = (
            results.win_counts.get("player_1", 0)
            + results.win_counts.get("player_3", 0)
        )
        random_wins = (
            results.win_counts.get("player_2", 0)
            + results.win_counts.get("player_4", 0)
        )

        # This is probabilistic, but with seed=42 naive should dominate
        assert naive_wins > random_wins
