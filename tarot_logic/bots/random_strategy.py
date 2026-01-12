"""Random bot strategy implementation."""

import random

from ..card import Card
from ..trick import Trick


class RandomStrategy:
    """Bot strategy that plays a random legal card.

    This strategy represents the simplest possible AI behavior: randomly
    selecting from available legal moves without any strategic consideration.
    Useful as a baseline for comparing more sophisticated strategies.
    """

    def choose_card(
        self,
        hand: list[Card],
        legal_moves: list[Card],
        current_trick: Trick,
    ) -> Card:
        """Choose a random card from the available legal moves.

        Args:
            hand: The bot's complete hand of cards (unused in random selection)
            legal_moves: Cards the bot can legally play
            current_trick: The current trick state (unused in random selection)

        Returns:
            A randomly selected card from legal_moves

        Raises:
            ValueError: If legal_moves is empty
        """
        if not legal_moves:
            raise ValueError("No legal moves available")

        return random.choice(legal_moves)

    def get_strategy_name(self) -> str:
        """Return the strategy name.

        Returns:
            "bot-random"
        """
        return "bot-random"
