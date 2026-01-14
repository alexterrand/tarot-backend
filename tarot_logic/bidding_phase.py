"""Bidding phase orchestration for Tarot game."""

from typing import TYPE_CHECKING

from .bidding import BiddingRound, BidType
from .contract import Contract

if TYPE_CHECKING:
    from .game_state import GameState
    from .card import Card


def run_bidding_phase(
    game_state: "GameState", bidding_strategies: dict[str, object]
) -> bool:
    """
    Run complete bidding phase for all players.

    Args:
        game_state: Current game state
        bidding_strategies: Dict mapping player_id to BiddingStrategy instance

    Returns:
        True if someone took, False if all passed
    """
    player_ids = [p.player_id for p in game_state.players]
    starting_index = 0  # First player starts bidding

    # Create bidding round
    bidding_round = BiddingRound(player_ids, starting_index)
    game_state.bidding_round = bidding_round

    # Get bidding order
    bidding_order = bidding_round.get_bidding_order()

    print("\n=== PHASE D'ENCHÈRES ===")

    # Each player bids in order
    for player_id in bidding_order:
        player = game_state.get_player_by_id(player_id)
        if not player:
            continue

        # Get current highest bid
        current_highest = bidding_round.contract_type

        # Get strategy for this player
        strategy = bidding_strategies.get(player_id)
        if not strategy:
            # Default to PASS if no strategy
            chosen_bid = BidType.PASS
        else:
            # Bot chooses bid based on hand
            chosen_bid = strategy.choose_bid(player.hand, current_highest)

        # Add bid to round
        bidding_round.add_bid(player_id, chosen_bid)

        # Display bid
        bid_name = chosen_bid.value if chosen_bid != BidType.PASS else "Passe"
        print(f"{player_id}: {bid_name}")

    print()

    # Check if anyone took
    if not bidding_round.has_taker():
        print("Tous les joueurs ont passé. Partie annulée.")
        return False

    # Create contract
    taker_id = bidding_round.taker_id
    contract_type = bidding_round.contract_type

    print(f"Preneur: {taker_id}")
    print(f"Contrat: {bidding_round.get_contract_display_name()}")
    print()

    # Note: Contract will be finalized after dog phase (when we know final oudlers)
    # For now, we just mark who is taker
    return True


def run_dog_phase(
    game_state: "GameState",
    taker_id: str,
    dog_discard_strategy: object,
) -> list["Card"]:
    """
    Run dog phase: give dog to taker, taker discards cards.

    Args:
        game_state: Current game state
        taker_id: Player who took the contract
        dog_discard_strategy: Strategy for choosing discard

    Returns:
        List of cards discarded by taker
    """
    print("=== PHASE DU CHIEN ===")

    taker = game_state.get_player_by_id(taker_id)
    if not taker:
        raise ValueError(f"Taker {taker_id} not found")

    # Give dog to taker
    print(f"Le chien ({len(game_state.dog)} cartes) est donné au preneur {taker_id}")
    for card in game_state.dog:
        taker.add_cards_to_hand([card])

    # Taker chooses discard
    dog_size = len(game_state.dog)
    discarded = dog_discard_strategy.choose_discard(taker.hand, dog_size)

    # Remove discarded cards from taker's hand
    for card in discarded:
        taker.hand.remove(card)

    # Store discarded cards back in dog
    game_state.dog = discarded

    print(f"Preneur écarte {len(discarded)} cartes")
    print()

    return discarded


def finalize_contract(game_state: "GameState") -> Contract:
    """
    Finalize contract after dog phase (calculate oudlers and points needed).

    Args:
        game_state: Current game state

    Returns:
        Finalized contract

    Raises:
        ValueError: If bidding round not complete
    """
    if not game_state.bidding_round or not game_state.bidding_round.has_taker():
        raise ValueError("No taker found, cannot finalize contract")

    taker_id = game_state.bidding_round.taker_id
    contract_type = game_state.bidding_round.contract_type

    # Get taker's current hand (after discard)
    taker = game_state.get_player_by_id(taker_id)
    if not taker:
        raise ValueError(f"Taker {taker_id} not found")

    # Count oudlers in taker's hand
    oudlers_count = game_state.count_oudlers(taker.hand)

    # Calculate points needed
    points_needed = game_state.bidding_round.get_contract_points_needed(oudlers_count)

    # Create contract
    contract = Contract(
        taker_id=taker_id,
        contract_type=contract_type,
        oudlers_count=oudlers_count,
        points_needed=points_needed,
    )

    game_state.contract = contract

    print(f"Contrat finalisé: {contract.get_contract_name()}")
    print(f"Oudlers dans la main du preneur: {oudlers_count}")
    print(f"Points nécessaires: {points_needed}")
    print()

    return contract
