"""Naive bot strategy implementation."""

from ..card import Card, Suit
from ..trick import Trick


class NaiveStrategy:
    """Bot strategy that always plays the strongest legal card.

    This strategy implements a simple "greedy" approach: always play the card
    with the highest value, based on a multi-criteria strength calculation.

    Strength is determined by:
    1. Point value (primary): 0.5 to 4.5 points
    2. Rank value (tiebreaker): card rank
    3. Trump priority (contextual): trumps preferred over suited cards in ties
    """

    def choose_card(
        self,
        hand: list[Card],
        legal_moves: list[Card],
        current_trick: Trick,
    ) -> Card:
        """Choose the strongest card from the available legal moves.

        Args:
            hand: The bot's complete hand of cards (unused in naive selection)
            legal_moves: Cards the bot can legally play
            current_trick: The current trick state (unused in naive selection)

        Returns:
            The strongest card from legal_moves based on the strength metric

        Raises:
            ValueError: If legal_moves is empty
        """
        if not legal_moves:
            raise ValueError("No legal moves available")

        return max(legal_moves, key=self._card_strength)

    def _card_strength(self, card: Card) -> tuple[float, int, bool]:
        """Calculate card strength for comparison.

        The strength is represented as a tuple that will be compared
        lexicographically: higher values in earlier positions take precedence.

        Args:
            card: The card to evaluate

        Returns:
            A tuple of (points, rank_value, is_trump) for sorting:
            - points: Card point value (0.5-4.5)
            - rank_value: Numeric rank value
            - is_trump: True if trump card, False otherwise
        """
        return (
            card.get_points(),          # Primary: point value for scoring
            card.rank.get_value(),      # Tiebreaker: higher rank wins
            card.suit == Suit.TRUMP,    # Trump priority in complete ties
        )

    def get_strategy_name(self) -> str:
        """Return the strategy name.

        Returns:
            "bot-naive"
        """
        return "bot-naive"
