"""Bot strategies for discarding cards to the dog (écart)."""

from typing import Protocol

from ..card import Card, Suit, Rank


class DogDiscardStrategy(Protocol):
    """Protocol for dog discard strategies."""

    def choose_discard(self, hand: list[Card], dog_size: int) -> list[Card]:
        """
        Choose which cards to discard from hand to dog.

        Args:
            hand: Taker's hand (including dog cards)
            dog_size: Number of cards to discard

        Returns:
            List of cards to discard
        """
        ...


class MaxPointsDiscardStrategy:
    """
    Discard strategy that maximizes points in the dog.

    Rules:
    - CANNOT discard: Kings, Trumps (including 1 and 21), Excuse
    - CAN discard: Queens, Knights, Jacks, numbered suited cards
    - Goal: Put as many points as possible in dog
    """

    def choose_discard(self, hand: list[Card], dog_size: int) -> list[Card]:
        """
        Choose cards to discard to maximize dog points.

        Args:
            hand: Taker's full hand
            dog_size: Number of cards to discard (usually 6)

        Returns:
            Cards to discard (prioritize high-point non-protected cards)
        """
        # Separate cards into discardable and protected
        discardable = []
        protected = []

        for card in hand:
            if self._can_discard(card):
                discardable.append(card)
            else:
                protected.append(card)

        # Sort discardable cards by points (highest first)
        discardable.sort(key=lambda c: c.get_points(), reverse=True)

        # Take top N cards with highest points
        if len(discardable) < dog_size:
            # Debug: print what cards are protected
            protected_details = [f"{c.suit.value}-{c.rank}" for c in protected]
            raise ValueError(
                f"Not enough discardable cards! Have {len(discardable)}, need {dog_size}. "
                f"Protected: {len(protected)} cards: {protected_details}"
            )

        discard = discardable[:dog_size]

        # Debug: verify all cards in discard are legal
        for card in discard:
            if not self._can_discard(card):
                raise ValueError(f"Trying to discard illegal card: {card.suit.value}")

        return discard

    def _can_discard(self, card: Card) -> bool:
        """
        Check if a card can be legally discarded.

        Rules:
        - Cannot discard Kings
        - Cannot discard Trumps (any trump including 1 and 21)
        - Cannot discard Excuse

        Args:
            card: Card to check

        Returns:
            True if card can be discarded
        """
        # Excuse cannot be discarded
        if card.suit == Suit.EXCUSE:
            return False

        # Trumps cannot be discarded
        if card.suit == Suit.TRUMP:
            return False

        # Kings cannot be discarded
        if card.rank == Rank.KING:
            return False

        # All other cards can be discarded (Queens, Knights, Jacks, numbered)
        return True


class RandomDiscardStrategy:
    """Random discard strategy (for testing)."""

    import random

    def choose_discard(self, hand: list[Card], dog_size: int) -> list[Card]:
        """
        Choose random legal cards to discard.

        Args:
            hand: Taker's hand
            dog_size: Number of cards to discard

        Returns:
            Random selection of discardable cards
        """
        # Get all discardable cards
        discardable = [
            card
            for card in hand
            if card.suit not in [Suit.EXCUSE, Suit.TRUMP] and card.rank != Rank.KING
        ]

        if len(discardable) < dog_size:
            raise ValueError(
                f"Not enough discardable cards: {len(discardable)} < {dog_size}"
            )

        # Random selection
        import random

        return random.sample(discardable, dog_size)
