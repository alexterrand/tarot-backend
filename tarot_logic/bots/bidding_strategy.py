"""Bot bidding strategies for Tarot game."""

from typing import Protocol

from ..card import Card, Suit
from ..bidding import BidType


class BiddingStrategy(Protocol):
    """Protocol for bot bidding strategies."""

    def choose_bid(
        self, hand: list[Card], current_highest_bid: BidType | None
    ) -> BidType:
        """
        Choose a bid based on hand strength.

        Args:
            hand: Bot's current hand
            current_highest_bid: Highest bid so far (None if no one has bid yet)

        Returns:
            Chosen bid type
        """
        ...


class PointBasedBiddingStrategy:
    """
    Bidding strategy based on hand point percentage relative to contract needs.

    Logic:
    - Pass if hand strength < 40% of base contract (51 pts) [relaxed for testing]
    - Petite if >= 40% (>= 20.4 pts)
    - Garde if >= 60% (>= 30.6 pts)
    - Garde Sans if >= 80% (>= 40.8 pts)
    - Garde Contre if >= 95% (>= 48.45 pts)
    """

    BASE_CONTRACT_POINTS = 51.0  # Base threshold for 1 oudler

    def choose_bid(
        self, hand: list[Card], current_highest_bid: BidType | None
    ) -> BidType:
        """
        Choose bid based on hand points percentage.

        Args:
            hand: Bot's hand
            current_highest_bid: Current highest bid (or None)

        Returns:
            Bid choice
        """
        hand_points = self._calculate_hand_strength(hand)
        percentage = (hand_points / self.BASE_CONTRACT_POINTS) * 100

        # Determine bid based on percentage thresholds
        if percentage >= 95:
            desired_bid = BidType.GARDE_CONTRE
        elif percentage >= 80:
            desired_bid = BidType.GARDE_SANS
        elif percentage >= 60:
            desired_bid = BidType.GARDE
        elif percentage >= 40:
            desired_bid = BidType.PETITE
        else:
            desired_bid = BidType.PASS

        # Only bid if we can beat current highest bid
        if current_highest_bid is None:
            # First bidder
            return desired_bid

        if desired_bid == BidType.PASS or desired_bid <= current_highest_bid:
            # Can't or won't beat current bid
            return BidType.PASS

        return desired_bid

    def _calculate_hand_strength(self, hand: list[Card]) -> float:
        """
        Calculate total point value of hand.

        Args:
            hand: List of cards

        Returns:
            Sum of card points
        """
        return sum(card.get_points() for card in hand)

    def _count_oudlers(self, hand: list[Card]) -> int:
        """
        Count oudlers in hand.

        Args:
            hand: List of cards

        Returns:
            Number of oudlers (0-3)
        """
        oudlers = 0
        for card in hand:
            if card.suit == Suit.EXCUSE:
                oudlers += 1
            elif card.suit == Suit.TRUMP and card.value in [1, 21]:
                oudlers += 1
        return oudlers


class RandomBiddingStrategy:
    """Random bidding strategy (for testing/baseline)."""

    import random

    def choose_bid(
        self, hand: list[Card], current_highest_bid: BidType | None
    ) -> BidType:
        """
        Choose random legal bid.

        Args:
            hand: Bot's hand (unused)
            current_highest_bid: Current highest bid

        Returns:
            Random legal bid
        """
        # Always pass for now (simplest baseline)
        return BidType.PASS
