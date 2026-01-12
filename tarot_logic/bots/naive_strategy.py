"""Naive bot strategy implementation."""

from . import bot_helpers
from ..card import Card, Suit
from ..trick import Trick


class NaiveStrategy:
    """Bot strategy that plays the strongest legal card with special card logic.

    This strategy implements a "greedy" approach with smart handling of
    special cards (Petit and Excuse):

    Decision Priority:
    1. Play Petit if safe (all opponents played) - Active play for 4.5pts
    2. Protect Petit if unsafe - Filter from options
    3. Play Excuse intelligently - On low-value tricks or when cannot win
    4. Play strongest card - Default greedy behavior

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
        """Choose the best card using special card logic + strength.

        Decision flow:
        1. Play Petit if safe (all opponents played)
        2. Filter unsafe Petit from legal moves
        3. Check if Excuse should be played (low-value trick or cannot win)
        4. Otherwise, play the strongest remaining card

        Args:
            hand: The bot's complete hand of cards
            legal_moves: Cards the bot can legally play
            current_trick: The current trick state

        Returns:
            The best card to play based on the decision flow

        Raises:
            ValueError: If legal_moves is empty
        """
        if not legal_moves:
            raise ValueError("No legal moves available")

        # Step 1: Check if Petit is safe and present - PLAY IT (priority)
        petit = next((c for c in legal_moves if bot_helpers.is_petit(c)), None)
        if petit and bot_helpers.should_play_petit_safe(petit, current_trick):
            return petit

        # Step 2: Filter Petit if unsafe to play
        safe_moves = bot_helpers.filter_petit_if_unsafe(legal_moves, current_trick)

        # Step 3: Check if Excuse should be prioritized
        asked_suit = current_trick.get_asked_suit()
        has_asked_suit = bot_helpers.has_asked_suit_in_hand(hand, asked_suit)

        excuse = bot_helpers.prioritize_excuse_on_low_value_trick(
            safe_moves, current_trick, hand, has_asked_suit
        )

        if excuse:
            return excuse

        # Step 4: Play strongest card from safe moves
        return max(safe_moves, key=self._card_strength)

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
