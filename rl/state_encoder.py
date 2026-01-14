"""State encoding for RL agents."""

import numpy as np
from tarot_logic.card import Card, Suit, Rank
from tarot_logic.trick import Trick
from tarot_logic.contract import Contract
from rl.card_encoder import CardEncoder
from typing import Optional


class StateEncoder:
    """Encodes full game state for neural network input."""

    def __init__(self):
        self.card_encoder = CardEncoder()
        self._state_dim = 506  # Total feature dimension

    def encode_state(
        self,
        hand: list[Card],
        legal_moves: list[Card],
        current_trick: Trick,
        position_in_trick: int,
        is_taker: bool,
        contract: Optional[Contract],
        trick_number: int,
        total_tricks: int = 26,  # 4-player game
    ) -> np.ndarray:
        """
        Convert game state to fixed-size vector.

        Args:
            hand: Cards currently in player's hand
            legal_moves: Cards that can be legally played
            current_trick: Current trick state
            position_in_trick: 0-3 (which position you play in this trick)
            is_taker: Whether this player is the taker
            contract: Current contract (None if abandoned)
            trick_number: Current trick number (1-indexed)
            total_tricks: Total tricks in game (default 26 for 4 players)

        Returns:
            np.ndarray of shape (506,)
        """
        features = []

        # 1. Your hand (78 dims)
        hand_vec = self.card_encoder.encode_hand(hand)
        features.append(hand_vec)

        # 2. Legal moves mask (78 dims)
        legal_mask = self.card_encoder.encode_legal_moves_mask(legal_moves)
        features.append(legal_mask)

        # 3. Current trick cards (4 × 78 = 312 dims)
        trick_cards = self._encode_trick_cards(current_trick)
        features.append(trick_cards)

        # 4. Position in trick (4 dims, one-hot)
        position_vec = np.zeros(4, dtype=np.float32)
        position_vec[position_in_trick] = 1.0
        features.append(position_vec)

        # 5. Trick context (27 dims)
        trick_context = self._encode_trick_context(current_trick)
        features.append(trick_context)

        # 6. Game context (7 dims)
        game_context = self._encode_game_context(is_taker, contract, hand, trick_number, total_tricks)
        features.append(game_context)

        # Concatenate all features
        state = np.concatenate(features)
        assert state.shape == (self._state_dim,), f"Expected {self._state_dim} dims, got {state.shape}"
        return state

    def _encode_trick_cards(self, trick: Trick) -> np.ndarray:
        """
        Encode cards played in current trick (4 × 78 = 312 dims).

        Each of 4 positions gets one-hot card encoding (or zeros if not played yet).
        """
        vec = np.zeros(4 * 78, dtype=np.float32)

        for i, card in enumerate(trick.cards):
            # Each player position gets 78-dim one-hot
            card_vec = self.card_encoder.encode_card(card)
            vec[i * 78 : (i + 1) * 78] = card_vec

        return vec

    def _encode_trick_context(self, trick: Trick) -> np.ndarray:
        """
        Encode trick context: asked suit, trump led, highest trump (27 dims).

        - Trump led: 1 binary
        - Suit context: 4 one-hot (clubs/diamonds/hearts/spades)
        - Highest trump rank: 22 one-hot (trump 1-21, plus "no trump")
        Total: 1 + 4 + 22 = 27 dims
        """
        vec = np.zeros(27, dtype=np.float32)

        # Get asked suit
        asked_suit = trick.get_asked_suit() if len(trick.cards) > 0 else None

        # Is trump led? (binary)
        vec[0] = 1.0 if asked_suit == Suit.TRUMP else 0.0

        # Suit context (4 dims, one-hot)
        if asked_suit in [Suit.CLUBS, Suit.DIAMONDS, Suit.HEARTS, Suit.SPADES]:
            suit_idx = [Suit.CLUBS, Suit.DIAMONDS, Suit.HEARTS, Suit.SPADES].index(asked_suit)
            vec[1 + suit_idx] = 1.0

        # Highest trump played (22 dims: 0=none, 1-21=trump rank)
        highest_trump = trick.get_highest_trump()
        if highest_trump is not None:
            trump_rank = highest_trump.rank.get_value()  # Normalized value (1-21)
            vec[5 + trump_rank] = 1.0
        else:
            vec[5] = 1.0  # No trump played yet

        return vec

    def _encode_game_context(
        self,
        is_taker: bool,
        contract: Optional[Contract],
        hand: list[Card],
        trick_number: int,
        total_tricks: int,
    ) -> np.ndarray:
        """
        Encode game context: taker status, contract, oudlers, progress (7 dims).

        - Am I taker: 1 binary
        - Contract type: 4 one-hot (petite/garde/garde_sans/garde_contre)
        - Oudlers in hand: 1 float (0-3)
        - Trick progress: 1 float (0-1)
        Total: 1 + 4 + 1 + 1 = 7 dims
        """
        vec = np.zeros(7, dtype=np.float32)

        # Am I the taker?
        vec[0] = 1.0 if is_taker else 0.0

        # Contract type (one-hot)
        if contract is not None:
            contract_types = ["petite", "garde", "garde_sans", "garde_contre"]
            contract_name = contract.contract_type.name.lower()
            if contract_name in contract_types:
                contract_idx = contract_types.index(contract_name)
                vec[1 + contract_idx] = 1.0

        # Count oudlers in hand (Petit, 21, Excuse)
        oudlers = [
            card
            for card in hand
            if (card.suit == Suit.TRUMP and card.rank.value in [1, 21]) or card.suit == Suit.EXCUSE
        ]
        vec[5] = float(len(oudlers))

        # Trick progress (normalized 0-1)
        vec[6] = trick_number / total_tricks

        return vec

    def get_state_dim(self) -> int:
        """Return total state dimension."""
        return self._state_dim
