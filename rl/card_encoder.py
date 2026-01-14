"""Card encoding utilities for RL agents."""

import numpy as np
from tarot_logic.card import Card, Suit, Rank, rank_from_int
from typing import Dict, Tuple


class CardEncoder:
    """Encodes Tarot cards as one-hot vectors for neural networks."""

    def __init__(self):
        # Build card to index mapping
        self._card_to_idx: Dict[Tuple[Suit, Rank], int] = {}
        self._idx_to_card: Dict[int, Tuple[Suit, Rank]] = {}

        idx = 0
        # Trumps (1-21)
        for rank_val in range(1, 22):
            rank = rank_from_int(rank_val, is_trump=True)
            self._card_to_idx[(Suit.TRUMP, rank)] = idx
            self._idx_to_card[idx] = (Suit.TRUMP, rank)
            idx += 1

        # Excuse
        self._card_to_idx[(Suit.EXCUSE, Rank.EXCUSE)] = idx
        self._idx_to_card[idx] = (Suit.EXCUSE, Rank.EXCUSE)
        idx += 1

        # Suited cards (each suit: 1-14)
        for suit in [Suit.CLUBS, Suit.DIAMONDS, Suit.HEARTS, Suit.SPADES]:
            for rank_val in range(1, 15):
                rank = rank_from_int(rank_val, is_trump=False)
                self._card_to_idx[(suit, rank)] = idx
                self._idx_to_card[idx] = (suit, rank)
                idx += 1

        assert idx == 78, f"Expected 78 cards, got {idx}"

    def encode_card(self, card: Card) -> np.ndarray:
        """
        Convert a single card to one-hot vector.

        Returns:
            np.ndarray of shape (78,) with 1.0 at card index, 0.0 elsewhere
        """
        vec = np.zeros(78, dtype=np.float32)
        idx = self._card_to_idx[(card.suit, card.rank)]
        vec[idx] = 1.0
        return vec

    def encode_hand(self, hand: list[Card]) -> np.ndarray:
        """
        Encode hand as multi-hot vector (sum of one-hot card vectors).

        Args:
            hand: List of cards in hand

        Returns:
            np.ndarray of shape (78,) with 1.0 for each card present
        """
        vec = np.zeros(78, dtype=np.float32)
        for card in hand:
            idx = self._card_to_idx[(card.suit, card.rank)]
            vec[idx] = 1.0
        return vec

    def encode_legal_moves_mask(self, legal_moves: list[Card]) -> np.ndarray:
        """
        Create binary mask for legal moves.

        Returns:
            np.ndarray of shape (78,) with 1.0 for legal cards, 0.0 for illegal
        """
        return self.encode_hand(legal_moves)

    def get_card_index(self, card: Card) -> int:
        """Get the index of a card (0-77)."""
        return self._card_to_idx[(card.suit, card.rank)]

    def decode_card_index(self, idx: int) -> Card:
        """
        Convert card index back to Card object.

        Args:
            idx: Card index (0-77)

        Returns:
            Card object
        """
        suit, rank = self._idx_to_card[idx]
        return Card(suit=suit, rank=rank)

    @property
    def num_cards(self) -> int:
        """Total number of cards in Tarot deck."""
        return 78
