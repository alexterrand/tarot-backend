"""Contract management for Tarot game."""

from typing import TYPE_CHECKING

from .bidding import BidType

if TYPE_CHECKING:
    from .card import Card


class Contract:
    """Represents a Tarot contract after bidding is complete."""

    def __init__(
        self,
        taker_id: str,
        contract_type: BidType,
        oudlers_count: int,
        points_needed: int,
    ):
        """
        Initialize a contract.

        Args:
            taker_id: Player ID who took the contract
            contract_type: Type of contract (Petite, Garde, etc.)
            oudlers_count: Number of oudlers in taker's cards
            points_needed: Points threshold to make the contract (36/41/51/56)
        """
        self.taker_id = taker_id
        self.contract_type = contract_type
        self.oudlers_count = oudlers_count
        self.points_needed = points_needed
        self.points_achieved: float = 0.0
        self.success: bool = False

    def calculate_score(self, taker_cards: list["Card"]) -> float:
        """
        Calculate total points won by the taker team.

        Args:
            taker_cards: All cards won by taker team (taker's tricks + dog)

        Returns:
            Total points (sum of card values)
        """
        self.points_achieved = sum(card.get_points() for card in taker_cards)
        self.success = self.points_achieved >= self.points_needed
        return self.points_achieved

    def evaluate_success(self) -> bool:
        """
        Determine if contract was made.

        Returns:
            True if taker achieved required points
        """
        return self.success

    def get_multiplier(self) -> float:
        """
        Get scoring multiplier for this contract.

        V1: Always returns 1.0
        V5: Will return 2.0 for GARDE_SANS, 4.0 for GARDE_CONTRE

        Returns:
            Contract multiplier
        """
        # V1: No multipliers yet
        return 1.0

    def get_contract_name(self) -> str:
        """
        Get human-readable contract name.

        Returns:
            Contract name string
        """
        names = {
            BidType.PETITE: "Petite",
            BidType.GARDE: "Garde",
            BidType.GARDE_SANS: "Garde Sans le Chien",
            BidType.GARDE_CONTRE: "Garde Contre le Chien",
        }
        return names.get(self.contract_type, "Unknown")

    def __str__(self) -> str:
        """String representation of the contract."""
        return f"{self.get_contract_name()} by {self.taker_id} ({self.points_achieved}/{self.points_needed} pts)"

    def __repr__(self) -> str:
        """Detailed representation."""
        return (
            f"Contract(taker={self.taker_id}, type={self.contract_type.value}, "
            f"oudlers={self.oudlers_count}, needed={self.points_needed}, "
            f"achieved={self.points_achieved}, success={self.success})"
        )
