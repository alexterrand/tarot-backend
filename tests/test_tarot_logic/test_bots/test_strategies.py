"""Unit tests for bot strategies."""

import pytest

from tarot_logic.bots import NaiveStrategy, RandomStrategy, create_strategy
from tarot_logic.card import Card, Rank, Suit
from tarot_logic.trick import Trick


class TestRandomStrategy:
    """Test suite for RandomStrategy."""

    def test_chooses_from_legal_moves(self):
        """RandomStrategy should only choose from legal moves."""
        strategy = RandomStrategy()

        hand = [
            Card(Suit.HEARTS, Rank.ACE),
            Card(Suit.HEARTS, Rank.KING),
            Card(Suit.HEARTS, Rank.QUEEN),
        ]
        legal_moves = [Card(Suit.HEARTS, Rank.ACE)]
        trick = Trick()

        # Run multiple times to ensure it always chooses legal move
        for _ in range(10):
            chosen = strategy.choose_card(hand, legal_moves, trick)
            assert chosen in legal_moves
            assert chosen == Card(Suit.HEARTS, Rank.ACE)

    def test_get_strategy_name(self):
        """Should return correct strategy name."""
        strategy = RandomStrategy()
        assert strategy.get_strategy_name() == "bot-random"


class TestNaiveStrategy:
    """Test suite for NaiveStrategy."""

    def test_chooses_strongest_by_points(self):
        """NaiveStrategy should choose card with highest points."""
        strategy = NaiveStrategy()

        legal_moves = [
            Card(Suit.HEARTS, Rank.TWO),  # 0.5 points
            Card(Suit.HEARTS, Rank.KING),  # 4.5 points
            Card(Suit.HEARTS, Rank.SEVEN),  # 0.5 points
        ]

        chosen = strategy.choose_card(legal_moves, legal_moves, Trick())
        assert chosen == Card(Suit.HEARTS, Rank.KING)

    def test_chooses_highest_rank_on_tie(self):
        """Should choose highest rank when points are equal."""
        strategy = NaiveStrategy()

        legal_moves = [
            Card(Suit.HEARTS, Rank.TWO),  # 0.5 points, rank 2
            Card(Suit.HEARTS, Rank.SEVEN),  # 0.5 points, rank 7
            Card(Suit.HEARTS, Rank.THREE),  # 0.5 points, rank 3
        ]

        chosen = strategy.choose_card(legal_moves, legal_moves, Trick())
        assert chosen == Card(Suit.HEARTS, Rank.SEVEN)

    def test_prefers_trump_on_complete_tie(self):
        """Should prefer trump when points and rank are similar."""
        strategy = NaiveStrategy()

        # Cards with same points (0.5) but trump should be preferred
        legal_moves = [
            Card(Suit.HEARTS, Rank.SEVEN),  # 0.5 points, rank 7
            Card(Suit.TRUMP, Rank.TRUMP_7),  # 0.5 points, trump rank 107
        ]

        chosen = strategy.choose_card(legal_moves, legal_moves, Trick())
        # Trump 7 has higher rank value (107 vs 7)
        assert chosen == Card(Suit.TRUMP, Rank.TRUMP_7)

    def test_oudler_priority(self):
        """Should prioritize Oudlers (Bouts) which have high point values."""
        strategy = NaiveStrategy()

        legal_moves = [
            Card(Suit.HEARTS, Rank.KING),  # 4.5 points
            Card(Suit.TRUMP, Rank.TRUMP_21),  # 4.5 points, Oudler
            Card(Suit.EXCUSE, Rank.EXCUSE),  # 4.5 points, Oudler
        ]

        chosen = strategy.choose_card(legal_moves, legal_moves, Trick())
        # All have same points (4.5), trump 21 has highest rank value
        assert chosen == Card(Suit.TRUMP, Rank.TRUMP_21)

    def test_get_strategy_name(self):
        """Should return correct strategy name."""
        strategy = NaiveStrategy()
        assert strategy.get_strategy_name() == "bot-naive"

    def test_uses_helpers_for_special_cards(self):
        """NaiveStrategy should use helpers to protect Petit and play Excuse."""
        strategy = NaiveStrategy()

        # Scenario: Petit in hand but unsafe (trump 10 already played)
        trick = Trick()
        trick.add_card(Card(Suit.HEARTS, Rank.ACE), 0)
        trick.add_card(Card(Suit.TRUMP, Rank.TRUMP_10), 1)

        hand = [
            Card(Suit.TRUMP, Rank.TRUMP_1),   # Petit (unsafe)
            Card(Suit.TRUMP, Rank.TRUMP_5),
            Card(Suit.EXCUSE, Rank.EXCUSE),
        ]
        legal_moves = [
            Card(Suit.TRUMP, Rank.TRUMP_1),
            Card(Suit.TRUMP, Rank.TRUMP_5),
            Card(Suit.EXCUSE, Rank.EXCUSE),
        ]

        chosen = strategy.choose_card(hand, legal_moves, trick)

        # Should play Excuse (low value trick + cannot win)
        # NOT Petit (unsafe) or Trump 5 (would waste trump)
        assert chosen == Card(Suit.EXCUSE, Rank.EXCUSE)


class TestStrategyFactory:
    """Test suite for create_strategy factory function."""

    def test_create_random_strategy(self):
        """Factory should create RandomStrategy."""
        strategy = create_strategy("bot-random")
        assert isinstance(strategy, RandomStrategy)
        assert strategy.get_strategy_name() == "bot-random"

    def test_create_naive_strategy(self):
        """Factory should create NaiveStrategy."""
        strategy = create_strategy("bot-naive")
        assert isinstance(strategy, NaiveStrategy)
        assert strategy.get_strategy_name() == "bot-naive"

    def test_unknown_strategy_raises(self):
        """Factory should raise ValueError for unknown strategy."""
        with pytest.raises(ValueError, match="Unknown strategy"):
            create_strategy("bot-unknown")

    def test_error_message_lists_available_strategies(self):
        """Error message should list available strategies."""
        with pytest.raises(ValueError, match="bot-random"):
            create_strategy("bot-invalid")
        with pytest.raises(ValueError, match="bot-naive"):
            create_strategy("bot-invalid")
