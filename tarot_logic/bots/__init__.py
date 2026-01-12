"""Bot strategy module for AI decision-making.

This module implements the Strategy Pattern for bot AI, allowing different
decision-making strategies to be plugged in without modifying the game logic.

Available Strategies:
    - RandomStrategy: Plays a random legal card
    - NaiveStrategy: Always plays the strongest legal card

Helper Module:
    - bot_helpers: Reusable functions for special card logic (Petit, Excuse)
"""

from . import bot_helpers
from .naive_strategy import NaiveStrategy
from .random_strategy import RandomStrategy
from .strategy import BotStrategy

__all__ = [
    "BotStrategy",
    "RandomStrategy",
    "NaiveStrategy",
    "create_strategy",
    "bot_helpers",
]


def create_strategy(strategy_name: str) -> BotStrategy:
    """Factory function to create bot strategies by name.

    This factory provides a centralized way to instantiate strategies,
    ensuring consistency and simplifying strategy management.

    Args:
        strategy_name: Name of the strategy to create.
            Valid values: "bot-random", "bot-naive"

    Returns:
        A strategy instance conforming to the BotStrategy protocol

    Raises:
        ValueError: If strategy_name is not recognized

    Examples:
        >>> random_bot = create_strategy("bot-random")
        >>> naive_bot = create_strategy("bot-naive")
    """
    strategies = {
        "bot-random": RandomStrategy(),
        "bot-naive": NaiveStrategy(),
    }

    if strategy_name not in strategies:
        available = ", ".join(strategies.keys())
        raise ValueError(
            f"Unknown strategy: '{strategy_name}'. Available strategies: {available}"
        )

    return strategies[strategy_name]
