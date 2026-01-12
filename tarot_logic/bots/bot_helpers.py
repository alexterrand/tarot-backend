"""Reusable helper functions for bot decision-making.

This module provides pure functions that analyze game state and provide
recommendations for playing special cards (Petit, Excuse) intelligently.
These helpers can be used by any bot strategy.
"""

from typing import Optional
from ..card import Card, Suit, Rank
from ..trick import Trick


# ============================================================================
# PETIT (1 d'Atout) HELPERS
# ============================================================================

def is_petit(card: Card) -> bool:
    """Check if card is the Petit (1 d'Atout).

    Args:
        card: Card to check

    Returns:
        True if card is the Petit, False otherwise
    """
    return card.suit == Suit.TRUMP and card.rank == Rank.TRUMP_1


def should_play_petit_safe(
    petit: Card,
    trick: Trick,
    num_players: int = 4
) -> bool:
    """Determine if it's safe to play the Petit.

    Safe conditions:
    1. All opponents have already played (bot is last to play)

    Unsafe conditions:
    1. Opponents haven't played yet (bot is NOT last)
    2. The highest trump in current trick was played by an opponent

    Args:
        petit: The Petit card
        trick: Current trick state
        num_players: Total number of players (default 4)

    Returns:
        True if safe to play the Petit, False otherwise
    """
    # Safe condition: All opponents have played (bot is last)
    num_cards_played = len(trick.cards)
    if num_cards_played == num_players - 1:
        return True  # Bot is last to play, safe

    # Unsafe condition: Opponents haven't played yet
    # Check if highest trump was played by opponent
    highest_trump = trick.get_highest_trump()
    if highest_trump:
        # If there's a trump higher than Petit, it's unsafe
        if highest_trump.rank.get_value() > Rank.TRUMP_1.get_value():
            return False

    # Default unsafe if not last
    return False


def filter_petit_if_unsafe(
    legal_moves: list[Card],
    trick: Trick,
    num_players: int = 4
) -> list[Card]:
    """Remove Petit from legal moves if it's unsafe to play.

    This function checks if the Petit is in legal_moves and removes it
    if playing it would be unsafe. If the Petit is the ONLY legal move,
    it will be kept (forced to play).

    Args:
        legal_moves: List of cards bot can legally play
        trick: Current trick state
        num_players: Total number of players (default 4)

    Returns:
        Filtered list without Petit if unsafe, or original list if safe/no Petit
    """
    petit = next((c for c in legal_moves if is_petit(c)), None)

    if not petit:
        return legal_moves  # No Petit in legal moves

    if should_play_petit_safe(petit, trick, num_players):
        return legal_moves  # Safe to play Petit

    # Unsafe: try to remove Petit from options
    filtered = [c for c in legal_moves if c != petit]

    # If Petit is the ONLY legal move, must play it (forced)
    return filtered if filtered else legal_moves


# ============================================================================
# EXCUSE HELPERS
# ============================================================================

def is_excuse(card: Card) -> bool:
    """Check if card is the Excuse.

    Args:
        card: Card to check

    Returns:
        True if card is the Excuse, False otherwise
    """
    return card.suit == Suit.EXCUSE


def calculate_trick_value(trick: Trick) -> float:
    """Calculate total point value of cards in current trick.

    Removes 0.5 points per card to get the actual strategic value.
    (In Tarot, each card is worth minimum 0.5 points in scoring)

    Args:
        trick: Current trick state

    Returns:
        Sum of card points minus 0.5 per card
    """
    total_points = sum(card.get_points() for card in trick.cards)
    num_cards = len(trick.cards)
    return total_points - (0.5 * num_cards)


def get_best_trump_in_hand(hand: list[Card]) -> Optional[Card]:
    """Get the highest trump card in hand.

    Args:
        hand: Bot's hand of cards

    Returns:
        Highest trump card, or None if no trumps in hand
    """
    trumps = [c for c in hand if c.suit == Suit.TRUMP]
    if not trumps:
        return None
    return max(trumps, key=lambda c: c.rank.get_value())


def can_win_trick_with_trump(hand: list[Card], trick: Trick) -> bool:
    """Check if bot can win the trick by playing trump.

    Args:
        hand: Bot's hand of cards
        trick: Current trick state

    Returns:
        True if bot has a trump higher than highest trump in trick
    """
    best_trump = get_best_trump_in_hand(hand)
    if not best_trump:
        return False  # No trump in hand

    highest_trump_in_trick = trick.get_highest_trump()
    if not highest_trump_in_trick:
        return True  # No trump in trick, bot's trump will win

    # Check if bot's best trump beats the trick's highest trump
    return best_trump.rank.get_value() > highest_trump_in_trick.rank.get_value()


def should_play_excuse_to_save_trump(
    excuse: Card,
    trick: Trick,
    hand: list[Card],
    must_play_trump: bool,
    value_threshold: float = 1.0
) -> bool:
    """Determine if Excuse should be played to avoid wasting a trump.

    Excuse should be played when:
    1. Trick has low value (<= threshold) AND bot must play trump
    2. Bot must cut BUT cannot win the trick (stronger trump already played)

    Args:
        excuse: The Excuse card
        trick: Current trick state
        hand: Bot's complete hand
        must_play_trump: Whether bot is forced to play trump
        value_threshold: Points below which trick is "low value" (default 1.0)

    Returns:
        True if should play Excuse, False otherwise
    """
    if not must_play_trump:
        return False  # No need to save trump if not forced to play it

    # Condition 1: Low value trick
    trick_value = calculate_trick_value(trick)
    if trick_value <= value_threshold:
        return True  # Play Excuse on low-value trick

    # Condition 2: Cannot win trick with trump
    if not can_win_trick_with_trump(hand, trick):
        return True  # Play Excuse, will lose anyway

    return False


def prioritize_excuse_on_low_value_trick(
    legal_moves: list[Card],
    trick: Trick,
    hand: list[Card],
    has_asked_suit: bool,
    value_threshold: float = 1.0
) -> Optional[Card]:
    """Return Excuse if it should be prioritized.

    This checks if the Excuse should be played to:
    1. Save trump on low-value trick
    2. Avoid wasting trump when trick is already lost

    Args:
        legal_moves: List of cards bot can legally play
        trick: Current trick state
        hand: Bot's complete hand
        has_asked_suit: Whether bot has the asked suit in hand
        value_threshold: Points below which trick is "low value" (default 1.0)

    Returns:
        Excuse card if should be played, None otherwise
    """
    excuse = next((c for c in legal_moves if is_excuse(c)), None)

    if not excuse:
        return None  # No Excuse in legal moves

    # Must be forced to play trump (don't have asked suit)
    must_play_trump = not has_asked_suit

    if should_play_excuse_to_save_trump(
        excuse, trick, hand, must_play_trump, value_threshold
    ):
        return excuse

    return None


# ============================================================================
# GENERAL CONTEXT HELPERS
# ============================================================================

def get_bot_position_in_trick(trick: Trick, num_players: int = 4) -> int:
    """Get bot's position in the trick.

    Args:
        trick: Current trick state
        num_players: Total number of players (default 4)

    Returns:
        Position index (0 = first to play, num_players-1 = last to play)
    """
    return len(trick.cards)


def is_last_to_play(trick: Trick, num_players: int = 4) -> bool:
    """Check if bot is last to play in this trick.

    Args:
        trick: Current trick state
        num_players: Total number of players (default 4)

    Returns:
        True if bot is last to play, False otherwise
    """
    return get_bot_position_in_trick(trick, num_players) == num_players - 1


def has_higher_trumps_in_trick(reference_trump: Card, trick: Trick) -> bool:
    """Check if trick contains trumps higher than reference.

    Args:
        reference_trump: Trump card to compare against
        trick: Current trick state

    Returns:
        True if trick has higher trump, False otherwise
    """
    highest = trick.get_highest_trump()
    if not highest:
        return False
    return highest.rank.get_value() > reference_trump.rank.get_value()


def has_asked_suit_in_hand(hand: list[Card], asked_suit: Optional[Suit]) -> bool:
    """Check if hand contains cards of the asked suit.

    Args:
        hand: Bot's hand of cards
        asked_suit: The suit that was asked (None if no suit asked yet)

    Returns:
        True if hand has asked suit, False otherwise
    """
    if asked_suit is None:
        return True  # No suit asked, consider as having it
    return any(card.suit == asked_suit for card in hand)
