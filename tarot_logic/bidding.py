"""Bidding system for Tarot game."""

from enum import Enum
from dataclasses import dataclass
from typing import Optional


class BidType(Enum):
    """Types of bids in Tarot."""

    PASS = "pass"
    PETITE = "petite"  # Small - basic contract
    GARDE = "garde"  # Guard - same as petite in v1, no multiplier
    GARDE_SANS = "garde_sans"  # Guard without dog (2x multiplier in v5)
    GARDE_CONTRE = "garde_contre"  # Guard against (4x multiplier in v5)

    def __lt__(self, other):
        """Compare bid strength for determining highest bid."""
        if not isinstance(other, BidType):
            return NotImplemented

        # Ordering: PASS < PETITE < GARDE < GARDE_SANS < GARDE_CONTRE
        order = [
            BidType.PASS,
            BidType.PETITE,
            BidType.GARDE,
            BidType.GARDE_SANS,
            BidType.GARDE_CONTRE,
        ]
        return order.index(self) < order.index(other)

    def __gt__(self, other):
        """Greater than comparison."""
        if not isinstance(other, BidType):
            return NotImplemented
        return not self < other and self != other

    def __le__(self, other):
        """Less than or equal comparison."""
        if not isinstance(other, BidType):
            return NotImplemented
        return self < other or self == other

    def __ge__(self, other):
        """Greater than or equal comparison."""
        if not isinstance(other, BidType):
            return NotImplemented
        return self > other or self == other


@dataclass
class Bid:
    """Represents a single bid from a player."""

    player_id: str
    bid_type: BidType


class BiddingRound:
    """Manages a complete bidding round."""

    def __init__(self, player_ids: list[str], starting_player_index: int):
        """
        Initialize bidding round.

        Args:
            player_ids: List of player IDs in game order
            starting_player_index: Index of player who starts bidding
        """
        self.player_ids = player_ids
        self.starting_player_index = starting_player_index
        self.bids: list[Bid] = []
        self.taker_id: Optional[str] = None
        self.contract_type: Optional[BidType] = None

    def add_bid(self, player_id: str, bid_type: BidType) -> None:
        """
        Add a bid to the round.

        Args:
            player_id: ID of the bidding player
            bid_type: Type of bid being made
        """
        bid = Bid(player_id=player_id, bid_type=bid_type)
        self.bids.append(bid)

        # Update taker if this is a higher bid than PASS
        if bid_type != BidType.PASS:
            if self.contract_type is None or bid_type > self.contract_type:
                self.taker_id = player_id
                self.contract_type = bid_type

    def is_complete(self) -> bool:
        """
        Check if bidding round is complete.

        Returns:
            True if all players have bid
        """
        return len(self.bids) >= len(self.player_ids)

    def get_bidding_order(self) -> list[str]:
        """
        Get the order in which players should bid.

        Returns:
            List of player IDs in bidding order
        """
        num_players = len(self.player_ids)
        order = []
        for i in range(num_players):
            player_index = (self.starting_player_index + i) % num_players
            order.append(self.player_ids[player_index])
        return order

    def has_taker(self) -> bool:
        """
        Check if someone took (bid something other than PASS).

        Returns:
            True if there is a taker
        """
        return self.taker_id is not None

    def get_contract_points_needed(self, oudlers_count: int) -> int:
        """
        Calculate points needed to make the contract based on oudlers.

        Args:
            oudlers_count: Number of oudlers (0-3) in taker's cards

        Returns:
            Points threshold (36, 41, 51, or 56)
        """
        thresholds = {
            0: 56,  # No oudlers
            1: 51,  # 1 oudler
            2: 41,  # 2 oudlers
            3: 36,  # All 3 oudlers
        }
        return thresholds.get(oudlers_count, 56)

    def get_contract_multiplier(self) -> float:
        """
        Get scoring multiplier for the contract type.

        V1: Always returns 1.0 (no multipliers yet)
        V5: Will return 2.0 for GARDE_SANS, 4.0 for GARDE_CONTRE

        Returns:
            Contract multiplier
        """
        # V1: All contracts have multiplier 1.0
        return 1.0

    def get_contract_display_name(self) -> str:
        """
        Get human-readable contract name.

        Returns:
            Contract name in French
        """
        if self.contract_type is None:
            return "Aucun"

        names = {
            BidType.PETITE: "Petite",
            BidType.GARDE: "Garde",
            BidType.GARDE_SANS: "Garde Sans le Chien",
            BidType.GARDE_CONTRE: "Garde Contre le Chien",
        }
        return names.get(self.contract_type, "Inconnu")
