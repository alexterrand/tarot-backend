#!/usr/bin/env python3
"""Quick test script to verify the Tarot RL environment works."""

import sys
sys.path.insert(0, '/home/terrand/Work/tarot-project/backend')

from rl.tarot_env import TarotSingleAgentEnv


def test_environment():
    """Test basic environment functionality."""
    print("=" * 60)
    print("Testing Tarot RL Environment")
    print("=" * 60)

    # Create environment
    print("\n1. Creating environment...")
    env = TarotSingleAgentEnv(opponent_strategy="bot-naive")
    print(f"   ✓ Environment created")
    print(f"   - Observation space: {env.observation_space}")
    print(f"   - Action space: {env.action_space}")

    # Reset environment
    print("\n2. Resetting environment...")
    obs, info = env.reset()
    print(f"   ✓ Environment reset")
    print(f"   - Observation shape: {obs.shape}")
    print(f"   - Current player: {info['current_player']}")
    print(f"   - Is taker: {info.get('is_taker', 'N/A')}")

    # Play a few random steps
    print("\n3. Playing 5 random actions...")
    for step in range(5):
        # Get legal actions (check observation)
        legal_mask = obs[78:156]  # Legal moves mask is at positions 78-156
        legal_actions = [i for i in range(78) if legal_mask[i] > 0.5]

        if not legal_actions:
            print(f"   ✗ No legal actions available at step {step}")
            break

        # Sample random legal action
        import random
        action = random.choice(legal_actions)

        obs, reward, terminated, truncated, info = env.step(action)

        print(f"   Step {step + 1}: Action={action}, Reward={reward:.2f}, Done={terminated or truncated}")

        if terminated or truncated:
            print(f"   ✓ Episode finished after {step + 1} steps")
            break

    # Test multiple episodes
    print("\n4. Testing 3 full episodes...")
    for episode in range(3):
        obs, info = env.reset()
        done = False
        steps = 0
        total_reward = 0

        while not done and steps < 1000:  # Safety limit
            legal_mask = obs[78:156]
            legal_actions = [i for i in range(78) if legal_mask[i] > 0.5]

            if not legal_actions:
                print(f"   ✗ Episode {episode + 1}: No legal actions at step {steps}")
                break

            action = random.choice(legal_actions)
            obs, reward, terminated, truncated, info = env.step(action)
            total_reward += reward
            steps += 1
            done = terminated or truncated

        print(f"   Episode {episode + 1}: {steps} steps, Reward={total_reward:.2f}")

    print("\n" + "=" * 60)
    print("✓ All tests passed!")
    print("=" * 60)
    print("\nEnvironment is ready for training!")

    env.close()


if __name__ == "__main__":
    try:
        test_environment()
    except Exception as e:
        print(f"\n✗ Test failed with error:")
        print(f"   {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
