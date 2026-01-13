"""Pydantic models for simulation module."""

from pydantic import BaseModel, Field


class SimulationConfig(BaseModel):
    """Configuration for running a simulation."""

    num_games: int = Field(gt=0, description="Number of games to simulate")
    player_strategies: dict[str, str] = Field(
        description="Mapping of player IDs to strategy names (e.g., 'bot-naive', 'bot-random')"
    )
    seed: int | None = Field(
        default=None, description="Random seed for reproducibility (optional)"
    )


class GameResult(BaseModel):
    """Result of a single simulated game."""

    game_id: str
    game_number: int
    winner_player_id: str
    final_scores: dict[str, int]
    total_tricks: int


class SimulationResults(BaseModel):
    """Aggregated results from a simulation run."""

    total_games: int
    player_strategies: dict[str, str]
    win_counts: dict[str, int]
    win_rates: dict[str, float]
    avg_scores: dict[str, float]
    games_logged_to_supabase: int
