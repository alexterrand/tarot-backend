#!/usr/bin/env python3
"""Test script to verify that full games are being played correctly."""

import numpy as np
from rl.tarot_env import TarotSingleAgentEnv


def test_single_game():
    """Run a single game with verbose output to verify completeness."""
    print("=" * 60)
    print("Testing Single Game Completeness")
    print("=" * 60)

    # Create environment with verbose logging
    env = TarotSingleAgentEnv(
        opponent_strategy="bot-naive",
        reward_mode="sparse",
        verbose=True,
    )

    # Reset environment
    obs, info = env.reset()
    print(f"\n[RESET] Game started")
    print(f"  Initial observation shape: {obs.shape}")
    print(f"  Is taker: {info.get('is_taker', 'Unknown')}")

    # Play the game
    step_count = 0
    total_reward = 0.0

    while True:
        # Get legal action mask
        action_mask = env.action_masks()
        legal_actions = np.where(action_mask == 1)[0]

        print(f"\n[STEP {step_count + 1}] RL Agent's turn")
        print(f"  Legal actions: {len(legal_actions)}")

        # Choose random legal action
        action = np.random.choice(legal_actions)

        # Take step
        obs, reward, terminated, truncated, info = env.step(action)
        step_count += 1
        total_reward += reward

        if terminated or truncated:
            print(f"\n[EPISODE END] Total steps: {step_count}")
            print(f"  Total reward: {total_reward}")
            print(f"  Terminated: {terminated}, Truncated: {truncated}")
            break

    print("\n" + "=" * 60)
    print(f"Game completed successfully in {step_count} steps!")
    print("=" * 60)

    env.close()
    return step_count, total_reward


def test_multiple_games(n_games: int = 5):
    """Run multiple games to verify consistency."""
    print("\n" + "=" * 60)
    print(f"Testing {n_games} Games")
    print("=" * 60)

    env = TarotSingleAgentEnv(
        opponent_strategy="bot-naive",
        reward_mode="sparse",
        verbose=True,
    )

    steps_per_game = []
    rewards_per_game = []

    for i in range(n_games):
        print(f"\n{'=' * 60}")
        print(f"Game {i + 1}/{n_games}")
        print(f"{'=' * 60}")

        obs, info = env.reset()
        step_count = 0
        total_reward = 0.0

        while True:
            action_mask = env.action_masks()
            legal_actions = np.where(action_mask == 1)[0]
            action = np.random.choice(legal_actions)

            obs, reward, terminated, truncated, info = env.step(action)
            step_count += 1
            total_reward += reward

            if terminated or truncated:
                break

        steps_per_game.append(step_count)
        rewards_per_game.append(total_reward)

    env.close()

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Average steps per game: {np.mean(steps_per_game):.2f} (expected: 18)")
    print(f"Steps range: {min(steps_per_game)} - {max(steps_per_game)}")
    print(f"Average reward: {np.mean(rewards_per_game):.2f}")
    print(f"Win rate: {np.sum(rewards_per_game) / n_games * 100:.1f}%")
    print("=" * 60)


if __name__ == "__main__":
    # Test single game first
    test_single_game()

    # Then test multiple games
    test_multiple_games(n_games=5)
