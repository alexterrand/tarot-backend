"""Unit tests for Trick legal moves rules."""

import pytest

from tarot_logic.card import Card, Rank, Suit
from tarot_logic.trick import Trick


class TestTrumpAskedSuit:
    """Test suite for when trump is the asked suit."""

    def test_must_play_higher_trump_when_available(self):
        """When trump is asked and player has higher trump, must play it."""
        trick = Trick()
        trick.add_card(Card(Suit.TRUMP, Rank.TRUMP_10), 0)

        player_hand = [
            Card(Suit.TRUMP, Rank.TRUMP_5),   # Lower than 10
            Card(Suit.TRUMP, Rank.TRUMP_15),  # Higher than 10
            Card(Suit.TRUMP, Rank.TRUMP_20),  # Higher than 10
            Card(Suit.HEARTS, Rank.KING),
        ]

        legal_moves = trick.get_legal_moves(player_hand)

        # Must play trump 15 or 20 (or excuse if had one)
        assert Card(Suit.TRUMP, Rank.TRUMP_15) in legal_moves
        assert Card(Suit.TRUMP, Rank.TRUMP_20) in legal_moves
        assert Card(Suit.TRUMP, Rank.TRUMP_5) not in legal_moves  # Too low
        assert Card(Suit.HEARTS, Rank.KING) not in legal_moves     # Not trump

    def test_can_play_any_trump_when_no_higher(self):
        """When trump is asked and player has no higher trump, can play any trump."""
        trick = Trick()
        trick.add_card(Card(Suit.TRUMP, Rank.TRUMP_20), 0)

        player_hand = [
            Card(Suit.TRUMP, Rank.TRUMP_5),
            Card(Suit.TRUMP, Rank.TRUMP_10),
            Card(Suit.HEARTS, Rank.KING),
        ]

        legal_moves = trick.get_legal_moves(player_hand)

        # Can play any trump since both are lower than 20
        assert Card(Suit.TRUMP, Rank.TRUMP_5) in legal_moves
        assert Card(Suit.TRUMP, Rank.TRUMP_10) in legal_moves
        assert Card(Suit.HEARTS, Rank.KING) not in legal_moves

    def test_excuse_always_legal_with_trump_asked(self):
        """Excuse can always be played, even when trump is asked."""
        trick = Trick()
        trick.add_card(Card(Suit.TRUMP, Rank.TRUMP_10), 0)

        player_hand = [
            Card(Suit.TRUMP, Rank.TRUMP_5),
            Card(Suit.EXCUSE, Rank.EXCUSE),
        ]

        legal_moves = trick.get_legal_moves(player_hand)

        # Excuse is always legal
        assert Card(Suit.EXCUSE, Rank.EXCUSE) in legal_moves

    def test_first_trump_played_no_restriction(self):
        """When first to play trump (trick empty), no restriction."""
        trick = Trick()

        player_hand = [
            Card(Suit.TRUMP, Rank.TRUMP_5),
            Card(Suit.TRUMP, Rank.TRUMP_20),
            Card(Suit.HEARTS, Rank.KING),
        ]

        legal_moves = trick.get_legal_moves(player_hand)

        # Can play any card
        assert len(legal_moves) == 3
        assert all(card in legal_moves for card in player_hand)


class TestCuttingWithTrump:
    """Test suite for cutting (playing trump when cannot follow suit)."""

    def test_must_play_higher_trump_when_cutting(self):
        """When cutting and higher trump available, must play it."""
        trick = Trick()
        trick.add_card(Card(Suit.HEARTS, Rank.KING), 0)
        trick.add_card(Card(Suit.TRUMP, Rank.TRUMP_10), 1)

        player_hand = [
            Card(Suit.TRUMP, Rank.TRUMP_5),   # Lower
            Card(Suit.TRUMP, Rank.TRUMP_15),  # Higher
            Card(Suit.SPADES, Rank.ACE),
        ]

        legal_moves = trick.get_legal_moves(player_hand)

        # Must play trump 15 (higher than 10)
        assert Card(Suit.TRUMP, Rank.TRUMP_15) in legal_moves
        assert Card(Suit.TRUMP, Rank.TRUMP_5) not in legal_moves  # Too low
        assert Card(Suit.SPADES, Rank.ACE) not in legal_moves     # Not trump

    def test_can_play_any_trump_when_cutting_no_higher(self):
        """When cutting and no higher trump, can play any trump."""
        trick = Trick()
        trick.add_card(Card(Suit.HEARTS, Rank.KING), 0)
        trick.add_card(Card(Suit.TRUMP, Rank.TRUMP_20), 1)

        player_hand = [
            Card(Suit.TRUMP, Rank.TRUMP_5),
            Card(Suit.TRUMP, Rank.TRUMP_10),
            Card(Suit.SPADES, Rank.ACE),
        ]

        legal_moves = trick.get_legal_moves(player_hand)

        # Can play any trump (both lower than 20)
        assert Card(Suit.TRUMP, Rank.TRUMP_5) in legal_moves
        assert Card(Suit.TRUMP, Rank.TRUMP_10) in legal_moves
        assert Card(Suit.SPADES, Rank.ACE) not in legal_moves


class TestFollowingSuit:
    """Test suite for following suit (non-trump)."""

    def test_must_follow_suit_when_available(self):
        """When player has asked suit, must play it."""
        trick = Trick()
        trick.add_card(Card(Suit.HEARTS, Rank.KING), 0)

        player_hand = [
            Card(Suit.HEARTS, Rank.ACE),
            Card(Suit.HEARTS, Rank.SEVEN),
            Card(Suit.SPADES, Rank.KING),
            Card(Suit.TRUMP, Rank.TRUMP_10),
        ]

        legal_moves = trick.get_legal_moves(player_hand)

        # Must play hearts (or excuse if had one)
        assert Card(Suit.HEARTS, Rank.ACE) in legal_moves
        assert Card(Suit.HEARTS, Rank.SEVEN) in legal_moves
        assert Card(Suit.SPADES, Rank.KING) not in legal_moves
        assert Card(Suit.TRUMP, Rank.TRUMP_10) not in legal_moves

    def test_no_rank_restriction_when_following_suit(self):
        """When following suit (non-trump), can play any rank."""
        trick = Trick()
        trick.add_card(Card(Suit.HEARTS, Rank.KING), 0)  # High card

        player_hand = [
            Card(Suit.HEARTS, Rank.TWO),    # Low card
            Card(Suit.HEARTS, Rank.SEVEN),  # Low card
            Card(Suit.SPADES, Rank.ACE),
        ]

        legal_moves = trick.get_legal_moves(player_hand)

        # Can play any heart, no need to "go higher"
        assert Card(Suit.HEARTS, Rank.TWO) in legal_moves
        assert Card(Suit.HEARTS, Rank.SEVEN) in legal_moves


class TestExcuseRules:
    """Test suite for Excuse special rules."""

    def test_excuse_always_legal(self):
        """Excuse can always be played regardless of situation."""
        trick = Trick()
        trick.add_card(Card(Suit.HEARTS, Rank.KING), 0)

        player_hand = [
            Card(Suit.HEARTS, Rank.ACE),
            Card(Suit.EXCUSE, Rank.EXCUSE),
            Card(Suit.SPADES, Rank.KING),
        ]

        legal_moves = trick.get_legal_moves(player_hand)

        # Excuse is legal even though hearts must be followed
        assert Card(Suit.EXCUSE, Rank.EXCUSE) in legal_moves
        assert Card(Suit.HEARTS, Rank.ACE) in legal_moves
        assert Card(Suit.SPADES, Rank.KING) not in legal_moves
