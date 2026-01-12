"""Bot strategy protocol definition."""

from typing import Protocol

from ..card import Card
from ..trick import Trick


class BotStrategy(Protocol):
    """Protocol defining the interface for bot decision-making strategies.

    This protocol establishes a contract that all bot strategies must follow,
    enabling the Strategy Pattern for AI decision-making in the tarot game.
    """

    def choose_card(
        self,
        hand: list[Card],
        legal_moves: list[Card],
        current_trick: Trick,
    ) -> Card:
        """Choose a card to play from the available legal moves.

        Args:
            hand: The bot's complete hand of cards
            legal_moves: Cards the bot can legally play (subset of hand)
            current_trick: The current trick state for context

        Returns:
            The card to play (must be in legal_moves)

        Raises:
            ValueError: If legal_moves is empty or chosen card not in legal_moves
        """
        ...

    def get_strategy_name(self) -> str:
        """Return the strategy name for logging and debugging.

        Returns:
            A string identifier for the strategy (e.g., "bot-random", "bot-naive")
        """
        ...
