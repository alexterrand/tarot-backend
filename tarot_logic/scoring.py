"""Tarot scoring calculation logic."""

from typing import TYPE_CHECKING
from .bidding import BidType

if TYPE_CHECKING:
    from .contract import Contract


def calculate_player_scores(
    contract: "Contract",
    taker_points: float,
    player_ids: list[str],
    num_players: int,
) -> dict[str, int]:
    """
    Calculate final scores for all players based on contract result.

    Implements official Tarot scoring:
    - Base score = |taker_points - points_needed|
    - Apply contract multiplier (Petite=1, Garde=2, Garde Sans=3, Garde Contre=4)
    - Taker gets/loses: base_score × num_defenders
    - Each defender gets/loses: ±base_score

    Args:
        contract: Contract object with taker_id, type, points_needed
        taker_points: Points achieved by taker team
        player_ids: List of all player IDs
        num_players: Number of players (4 or 5)

    Returns:
        Dict mapping player_id to score gain/loss (zero-sum)

    Examples:
        >>> # Petite lost: taker needed 56, got 50 (diff = 6, mult = 1)
        >>> # Taker loses 6×3 = -18, each defender gains +6
        >>> # Total: -18 + 6 + 6 + 6 = 0 ✓

        >>> # Garde won: taker needed 41, got 49 (diff = 8, mult = 2)
        >>> # Final score = 8×2 = 16
        >>> # Taker gains 16×3 = +48, each defender loses -16
        >>> # Total: 48 - 16 - 16 - 16 = 0 ✓
    """
    # Base score = difference from threshold
    base_diff = abs(taker_points - contract.points_needed)

    # Contract multiplier
    contract_multipliers = {
        BidType.PETITE: 1,
        BidType.GARDE: 2,
        BidType.GARDE_SANS: 3,
        BidType.GARDE_CONTRE: 4,
    }
    contract_mult = contract_multipliers.get(contract.contract_type, 1)

    # Apply contract multiplier
    final_score = int(base_diff * contract_mult)

    # Number of defenders
    num_defenders = num_players - 1  # All except taker (for 4 players = 3 defenders)

    # Determine if contract won
    contract_won = taker_points >= contract.points_needed

    # Calculate scores
    scores = {}

    if contract_won:
        # Taker wins: gains final_score × num_defenders
        # Each defender loses final_score
        taker_gain = final_score * num_defenders

        for player_id in player_ids:
            if player_id == contract.taker_id:
                scores[player_id] = taker_gain
            else:
                scores[player_id] = -final_score
    else:
        # Taker loses: loses final_score × num_defenders
        # Each defender gains final_score
        taker_loss = -final_score * num_defenders

        for player_id in player_ids:
            if player_id == contract.taker_id:
                scores[player_id] = taker_loss
            else:
                scores[player_id] = final_score

    return scores
