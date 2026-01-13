"""Quick test script for Supabase integration.

Run this to verify that game logging works correctly.
"""

import sys
from app.services.game_service import GameService

def test_game_logging():
    """Test a simple 4-player game with logging."""
    print("=== Testing Supabase Game Logging ===\n")

    # Create game service
    service = GameService()

    # Create a 4-player game
    print("1. Creating game...")
    game_id = service.create_game(num_players=4, human_player_id="player_1")
    print(f"✓ Game created: {game_id}\n")

    # Get game state
    game_state_model = service.get_game_state(game_id)
    if not game_state_model:
        print("✗ Failed to get game state")
        return False

    print(f"2. Game state: {len(game_state_model.players)} players")
    print(f"   Current player: {game_state_model.current_player_id}\n")

    # Get player hand
    hand = service.get_player_hand(game_id, "player_1")
    if not hand:
        print("✗ Failed to get player hand")
        return False

    print(f"3. Player 1 hand: {len(hand.cards)} cards")
    print(f"   First card: {hand.cards[0].display_name}\n")

    # Get legal moves
    legal_moves = service.get_legal_moves(game_id, "player_1")
    print(f"4. Legal moves for player 1: {len(legal_moves)} cards")

    if not legal_moves:
        print("✗ No legal moves available")
        return False

    # Play first card
    first_card = legal_moves[0]
    print(f"   Playing: {first_card.display_name}")

    success, message = service.play_card(game_id, "player_1", first_card)
    if not success:
        print(f"✗ Failed to play card: {message}")
        return False

    print(f"✓ Card played: {message}\n")

    # Check if game is over (it shouldn't be after 1 card)
    game_state = service.games.get(game_id)
    if not game_state:
        print("✗ Game state lost")
        return False

    print(f"5. Game status:")
    print(f"   Cards in current trick: {len(game_state.current_trick)}")
    print(f"   Current player: {game_state.get_current_player().player_id}")
    print(f"   Game over: {game_state.is_game_over()}\n")

    print("=== Test Completed Successfully ===")
    print("\nCheck your Supabase dashboard:")
    print("  - games table should have 1 row")
    print("  - game_rounds table should have 1 row")
    print("  - tricks table should start filling as tricks complete")
    print("  - bot_decisions table should have decision entries")

    return True

if __name__ == "__main__":
    try:
        success = test_game_logging()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
