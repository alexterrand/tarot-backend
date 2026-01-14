#!/usr/bin/env python3
"""Evaluation script for trained Tarot RL agent."""

import argparse
from collections import defaultdict

from stable_baselines3 import PPO
from stable_baselines3.common.monitor import Monitor

from rl.tarot_env import TarotSingleAgentEnv


def evaluate_agent(
    model_path: str,
    opponent_strategy: str = "bot-naive",
    n_episodes: int = 100,
    deterministic: bool = True,
    reward_mode: str = "sparse",
):
    """
    Evaluate a trained RL agent.

    Args:
        model_path: Path to the trained model
        opponent_strategy: Strategy for opponent bots
        n_episodes: Number of episodes to evaluate
        deterministic: Use deterministic policy (greedy)
        reward_mode: Reward mode for environment

    Returns:
        Dictionary with evaluation metrics
    """
    print("=" * 60)
    print("Evaluating Tarot RL Agent")
    print("=" * 60)
    print(f"Model: {model_path}")
    print(f"Opponent: {opponent_strategy}")
    print(f"Episodes: {n_episodes}")
    print(f"Deterministic: {deterministic}")
    print("=" * 60)

    # Load model
    print("\nLoading model...")
    model = PPO.load(model_path)

    # Create environment
    env = Monitor(
        TarotSingleAgentEnv(
            opponent_strategy=opponent_strategy,
            reward_mode=reward_mode,
        )
    )

    # Evaluation metrics
    episode_rewards = []
    episode_lengths = []
    wins = 0
    losses = 0

    # Role-specific stats
    wins_as_taker = 0
    losses_as_taker = 0
    wins_as_defense = 0
    losses_as_defense = 0

    print(f"\nRunning {n_episodes} episodes...")

    for episode in range(n_episodes):
        obs, info = env.reset()
        episode_reward = 0
        episode_length = 0
        done = False

        is_taker = info.get("is_taker", False)

        while not done:
            action, _states = model.predict(obs, deterministic=deterministic)
            obs, reward, terminated, truncated, info = env.step(action)
            episode_reward += reward
            episode_length += 1
            done = terminated or truncated

        # Record metrics
        episode_rewards.append(episode_reward)
        episode_lengths.append(episode_length)

        # Count wins/losses
        if episode_reward > 0:
            wins += 1
            if is_taker:
                wins_as_taker += 1
            else:
                wins_as_defense += 1
        else:
            losses += 1
            if is_taker:
                losses_as_taker += 1
            else:
                losses_as_defense += 1

        if (episode + 1) % 10 == 0:
            avg_reward = sum(episode_rewards[-10:]) / 10
            print(f"Episode {episode + 1}/{n_episodes} - Avg Reward (last 10): {avg_reward:.3f}")

    # Compute summary statistics
    avg_reward = sum(episode_rewards) / len(episode_rewards)
    avg_length = sum(episode_lengths) / len(episode_lengths)
    win_rate = wins / n_episodes

    # Role-specific win rates
    total_taker = wins_as_taker + losses_as_taker
    total_defense = wins_as_defense + losses_as_defense

    win_rate_taker = wins_as_taker / total_taker if total_taker > 0 else 0
    win_rate_defense = wins_as_defense / total_defense if total_defense > 0 else 0

    # Print results
    print("\n" + "=" * 60)
    print("EVALUATION RESULTS")
    print("=" * 60)
    print(f"Episodes: {n_episodes}")
    print(f"Average Reward: {avg_reward:.3f}")
    print(f"Average Episode Length: {avg_length:.1f}")
    print()
    print(f"Overall Win Rate: {win_rate:.1%} ({wins}/{n_episodes})")
    print()
    print(f"Win Rate as Taker: {win_rate_taker:.1%} ({wins_as_taker}/{total_taker})")
    print(f"Win Rate as Defense: {win_rate_defense:.1%} ({wins_as_defense}/{total_defense})")
    print("=" * 60)

    env.close()

    return {
        "avg_reward": avg_reward,
        "avg_length": avg_length,
        "win_rate": win_rate,
        "wins": wins,
        "losses": losses,
        "win_rate_taker": win_rate_taker,
        "win_rate_defense": win_rate_defense,
        "wins_as_taker": wins_as_taker,
        "wins_as_defense": wins_as_defense,
        "total_taker": total_taker,
        "total_defense": total_defense,
    }


def main():
    """Parse arguments and run evaluation."""
    parser = argparse.ArgumentParser(description="Evaluate trained Tarot RL agent")

    parser.add_argument(
        "--model",
        type=str,
        required=True,
        help="Path to trained model (.zip file)",
    )

    parser.add_argument(
        "--opponent",
        type=str,
        default="bot-naive",
        help="Opponent strategy (bot-naive, bot-random, etc.)",
    )

    parser.add_argument(
        "--episodes",
        type=int,
        default=100,
        help="Number of evaluation episodes",
    )

    parser.add_argument(
        "--stochastic",
        action="store_true",
        help="Use stochastic policy instead of deterministic",
    )

    parser.add_argument(
        "--reward-mode",
        type=str,
        default="sparse",
        choices=["sparse", "dense"],
        help="Reward mode",
    )

    args = parser.parse_args()

    # Run evaluation
    results = evaluate_agent(
        model_path=args.model,
        opponent_strategy=args.opponent,
        n_episodes=args.episodes,
        deterministic=not args.stochastic,
        reward_mode=args.reward_mode,
    )


if __name__ == "__main__":
    main()
