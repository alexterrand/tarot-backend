"""Unit tests for bot helper functions."""

import pytest

from tarot_logic.bots import bot_helpers
from tarot_logic.card import Card, Rank, Suit
from tarot_logic.trick import Trick


class TestPetitHelpers:
    """Test suite for Petit helper functions."""

    def test_is_petit(self):
        """Should correctly identify the Petit."""
        petit = Card(Suit.TRUMP, Rank.TRUMP_1)
        assert bot_helpers.is_petit(petit) is True

        not_petit = Card(Suit.TRUMP, Rank.TRUMP_21)
        assert bot_helpers.is_petit(not_petit) is False

    def test_should_play_petit_safe_when_last(self):
        """Petit is safe when bot is last to play."""
        trick = Trick()
        trick.add_card(Card(Suit.HEARTS, Rank.ACE), 0)
        trick.add_card(Card(Suit.HEARTS, Rank.KING), 1)
        trick.add_card(Card(Suit.HEARTS, Rank.QUEEN), 2)
        # Bot is player 3 (last)

        petit = Card(Suit.TRUMP, Rank.TRUMP_1)
        assert bot_helpers.should_play_petit_safe(petit, trick, num_players=4) is True

    def test_should_not_play_petit_when_higher_trump_played(self):
        """Petit is unsafe when higher trump already played."""
        trick = Trick()
        trick.add_card(Card(Suit.HEARTS, Rank.ACE), 0)
        trick.add_card(Card(Suit.TRUMP, Rank.TRUMP_10), 1)
        # Bot is player 2, trump 10 is higher than Petit

        petit = Card(Suit.TRUMP, Rank.TRUMP_1)
        assert bot_helpers.should_play_petit_safe(petit, trick, num_players=4) is False

    def test_filter_petit_if_unsafe_removes_petit(self):
        """Filter should remove unsafe Petit from legal moves."""
        trick = Trick()
        trick.add_card(Card(Suit.TRUMP, Rank.TRUMP_15), 0)

        legal_moves = [
            Card(Suit.TRUMP, Rank.TRUMP_1),  # Petit (unsafe)
            Card(Suit.TRUMP, Rank.TRUMP_5),
            Card(Suit.TRUMP, Rank.TRUMP_10),
        ]

        filtered = bot_helpers.filter_petit_if_unsafe(legal_moves, trick)
        assert Card(Suit.TRUMP, Rank.TRUMP_1) not in filtered
        assert len(filtered) == 2


class TestExcuseHelpers:
    """Test suite for Excuse helper functions."""

    def test_is_excuse(self):
        """Should correctly identify the Excuse."""
        excuse = Card(Suit.EXCUSE, Rank.EXCUSE)
        assert bot_helpers.is_excuse(excuse) is True

        not_excuse = Card(Suit.TRUMP, Rank.TRUMP_21)
        assert bot_helpers.is_excuse(not_excuse) is False

    def test_calculate_trick_value_removes_base_points(self):
        """Should remove 0.5 points per card."""
        trick = Trick()
        trick.add_card(Card(Suit.HEARTS, Rank.KING), 0)  # 4.5pts
        trick.add_card(Card(Suit.HEARTS, Rank.TWO), 1)   # 0.5pts
        trick.add_card(Card(Suit.HEARTS, Rank.THREE), 2)  # 0.5pts
        # Total: 5.5pts, minus 3 × 0.5 = 4.0pts

        value = bot_helpers.calculate_trick_value(trick)
        assert value == 4.0

    def test_calculate_trick_value_low_cards(self):
        """Low-value cards should result in 0 strategic value."""
        trick = Trick()
        trick.add_card(Card(Suit.HEARTS, Rank.TWO), 0)    # 0.5pts
        trick.add_card(Card(Suit.HEARTS, Rank.THREE), 1)  # 0.5pts
        trick.add_card(Card(Suit.HEARTS, Rank.FOUR), 2)   # 0.5pts
        # Total: 1.5pts, minus 3 × 0.5 = 0pts

        value = bot_helpers.calculate_trick_value(trick)
        assert value == 0.0

    def test_get_best_trump_in_hand(self):
        """Should return highest trump in hand."""
        hand = [
            Card(Suit.TRUMP, Rank.TRUMP_5),
            Card(Suit.TRUMP, Rank.TRUMP_15),
            Card(Suit.TRUMP, Rank.TRUMP_10),
            Card(Suit.HEARTS, Rank.KING),
        ]

        best_trump = bot_helpers.get_best_trump_in_hand(hand)
        assert best_trump == Card(Suit.TRUMP, Rank.TRUMP_15)

    def test_can_win_trick_with_trump_yes(self):
        """Should return True if bot has higher trump."""
        trick = Trick()
        trick.add_card(Card(Suit.HEARTS, Rank.ACE), 0)
        trick.add_card(Card(Suit.TRUMP, Rank.TRUMP_10), 1)

        hand = [
            Card(Suit.TRUMP, Rank.TRUMP_15),  # Higher than 10
            Card(Suit.HEARTS, Rank.KING),
        ]

        assert bot_helpers.can_win_trick_with_trump(hand, trick) is True

    def test_can_win_trick_with_trump_no(self):
        """Should return False if bot cannot beat highest trump."""
        trick = Trick()
        trick.add_card(Card(Suit.HEARTS, Rank.ACE), 0)
        trick.add_card(Card(Suit.TRUMP, Rank.TRUMP_21), 1)  # 21 (highest)

        hand = [
            Card(Suit.TRUMP, Rank.TRUMP_15),  # Lower than 21
            Card(Suit.HEARTS, Rank.KING),
            Card(Suit.EXCUSE, Rank.EXCUSE),
        ]

        assert bot_helpers.can_win_trick_with_trump(hand, trick) is False

    def test_should_play_excuse_on_low_value_trick(self):
        """Should play Excuse on low-value trick when must cut."""
        trick = Trick()
        trick.add_card(Card(Suit.HEARTS, Rank.TWO), 0)    # 0.5pts
        trick.add_card(Card(Suit.HEARTS, Rank.THREE), 1)  # 0.5pts
        # Value = 1.0 - 1.0 = 0pts (low value)

        excuse = Card(Suit.EXCUSE, Rank.EXCUSE)
        hand = [
            excuse,
            Card(Suit.TRUMP, Rank.TRUMP_10),
        ]
        must_play_trump = True  # No hearts in hand

        assert bot_helpers.should_play_excuse_to_save_trump(
            excuse, trick, hand, must_play_trump, value_threshold=1.0
        ) is True

    def test_should_play_excuse_when_cannot_win_trick(self):
        """Should play Excuse when trump 21 present and bot has lower trumps."""
        trick = Trick()
        trick.add_card(Card(Suit.HEARTS, Rank.KING), 0)   # 4.5pts
        trick.add_card(Card(Suit.TRUMP, Rank.TRUMP_21), 1)  # 21 already played
        # Value = 9.0 - 1.0 = 8.0pts (high value BUT bot cannot win)

        excuse = Card(Suit.EXCUSE, Rank.EXCUSE)
        hand = [
            excuse,
            Card(Suit.TRUMP, Rank.TRUMP_15),  # Cannot beat 21
            Card(Suit.TRUMP, Rank.TRUMP_10),
        ]
        must_play_trump = True  # No hearts in hand

        # Should play Excuse because cannot win even though trick value is high
        assert bot_helpers.should_play_excuse_to_save_trump(
            excuse, trick, hand, must_play_trump, value_threshold=1.0
        ) is True

    def test_should_not_play_excuse_when_can_win_high_value_trick(self):
        """Should NOT play Excuse when can win high-value trick."""
        trick = Trick()
        trick.add_card(Card(Suit.HEARTS, Rank.KING), 0)    # 4.5pts
        trick.add_card(Card(Suit.TRUMP, Rank.TRUMP_10), 1)  # Trump 10
        # Value = 9.0 - 1.0 = 8.0pts (high value AND bot can win)

        excuse = Card(Suit.EXCUSE, Rank.EXCUSE)
        hand = [
            excuse,
            Card(Suit.TRUMP, Rank.TRUMP_21),  # Can beat trump 10
        ]
        must_play_trump = True

        # Should NOT play Excuse, should use trump 21 to win high-value trick
        assert bot_helpers.should_play_excuse_to_save_trump(
            excuse, trick, hand, must_play_trump, value_threshold=1.0
        ) is False

    def test_prioritize_excuse_on_low_value_trick(self):
        """Integration test for excuse prioritization."""
        trick = Trick()
        trick.add_card(Card(Suit.HEARTS, Rank.TWO), 0)
        trick.add_card(Card(Suit.HEARTS, Rank.THREE), 1)

        hand = [
            Card(Suit.EXCUSE, Rank.EXCUSE),
            Card(Suit.TRUMP, Rank.TRUMP_5),
            Card(Suit.TRUMP, Rank.TRUMP_10),
        ]
        legal_moves = [
            Card(Suit.EXCUSE, Rank.EXCUSE),
            Card(Suit.TRUMP, Rank.TRUMP_5),
            Card(Suit.TRUMP, Rank.TRUMP_10),
        ]
        has_asked_suit = False  # No hearts in hand

        result = bot_helpers.prioritize_excuse_on_low_value_trick(
            legal_moves, trick, hand, has_asked_suit
        )

        assert result == Card(Suit.EXCUSE, Rank.EXCUSE)

    def test_prioritize_excuse_when_21_present(self):
        """Should recommend Excuse when 21 is in trick and bot has lower trumps."""
        trick = Trick()
        trick.add_card(Card(Suit.HEARTS, Rank.KING), 0)
        trick.add_card(Card(Suit.TRUMP, Rank.TRUMP_21), 1)  # 21 present

        hand = [
            Card(Suit.EXCUSE, Rank.EXCUSE),
            Card(Suit.TRUMP, Rank.TRUMP_10),
            Card(Suit.TRUMP, Rank.TRUMP_15),
        ]
        legal_moves = [
            Card(Suit.EXCUSE, Rank.EXCUSE),
            Card(Suit.TRUMP, Rank.TRUMP_10),
            Card(Suit.TRUMP, Rank.TRUMP_15),
        ]
        has_asked_suit = False  # No hearts

        result = bot_helpers.prioritize_excuse_on_low_value_trick(
            legal_moves, trick, hand, has_asked_suit
        )

        # Should recommend Excuse since cannot win (21 present, best trump is 15)
        assert result == Card(Suit.EXCUSE, Rank.EXCUSE)


class TestGeneralHelpers:
    """Test suite for general context helper functions."""

    def test_get_bot_position_in_trick(self):
        """Should return correct position."""
        trick = Trick()
        assert bot_helpers.get_bot_position_in_trick(trick) == 0

        trick.add_card(Card(Suit.HEARTS, Rank.ACE), 0)
        assert bot_helpers.get_bot_position_in_trick(trick) == 1

        trick.add_card(Card(Suit.HEARTS, Rank.KING), 1)
        assert bot_helpers.get_bot_position_in_trick(trick) == 2

    def test_is_last_to_play(self):
        """Should correctly identify last position."""
        trick = Trick()
        trick.add_card(Card(Suit.HEARTS, Rank.ACE), 0)
        trick.add_card(Card(Suit.HEARTS, Rank.KING), 1)
        trick.add_card(Card(Suit.HEARTS, Rank.QUEEN), 2)
        # Bot would be player 3 (last in 4-player game)

        assert bot_helpers.is_last_to_play(trick, num_players=4) is True

    def test_has_asked_suit_in_hand(self):
        """Should check if hand has asked suit."""
        hand = [
            Card(Suit.HEARTS, Rank.ACE),
            Card(Suit.TRUMP, Rank.TRUMP_10),
        ]

        assert bot_helpers.has_asked_suit_in_hand(hand, Suit.HEARTS) is True
        assert bot_helpers.has_asked_suit_in_hand(hand, Suit.SPADES) is False
        assert bot_helpers.has_asked_suit_in_hand(hand, None) is True
