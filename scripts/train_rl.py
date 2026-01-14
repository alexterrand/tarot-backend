#!/usr/bin/env python3
"""Training script for Tarot RL agent using Stable-Baselines3 PPO."""

import argparse
import os
from pathlib import Path

from sb3_contrib import MaskablePPO
from sb3_contrib.common.wrappers import ActionMasker
from sb3_contrib.common.maskable.evaluation import evaluate_policy as maskable_evaluate_policy
from stable_baselines3.common.vec_env import SubprocVecEnv, DummyVecEnv
from stable_baselines3.common.callbacks import CheckpointCallback, BaseCallback
from stable_baselines3.common.monitor import Monitor

from rl.tarot_env import TarotSingleAgentEnv
from rl.config import RLConfig, DEFAULT_CONFIG
import numpy as np


class MaskableEvalCallback(BaseCallback):
    """Custom evaluation callback for MaskablePPO."""

    def __init__(
        self,
        eval_env,
        n_eval_episodes: int = 100,
        eval_freq: int = 10000,
        log_path: str = None,
        best_model_save_path: str = None,
        deterministic: bool = True,
    ):
        super().__init__()
        self.eval_env = eval_env
        self.n_eval_episodes = n_eval_episodes
        self.eval_freq = eval_freq
        self.log_path = log_path
        self.best_model_save_path = best_model_save_path
        self.deterministic = deterministic
        self.best_mean_reward = -np.inf
        self.last_mean_reward = 0.0

    def _on_step(self) -> bool:
        if self.n_calls % self.eval_freq == 0:
            # Evaluate the policy
            episode_rewards = []
            episode_lengths = []

            for _ in range(self.n_eval_episodes):
                obs, info = self.eval_env.reset()
                done = False
                episode_reward = 0.0
                episode_length = 0

                while not done:
                    # Get action mask (unwrap Monitor wrapper)
                    base_env = self.eval_env.env if hasattr(self.eval_env, 'env') else self.eval_env
                    action_masks = base_env.action_masks()

                    # Predict with mask
                    action, _ = self.model.predict(
                        obs,
                        action_masks=action_masks,
                        deterministic=self.deterministic,
                    )

                    # Convert numpy array to int if needed
                    if isinstance(action, np.ndarray):
                        action = int(action.item())

                    obs, reward, terminated, truncated, info = self.eval_env.step(action)
                    episode_reward += reward
                    episode_length += 1
                    done = terminated or truncated

                episode_rewards.append(episode_reward)
                episode_lengths.append(episode_length)

            mean_reward = np.mean(episode_rewards)
            std_reward = np.std(episode_rewards)
            mean_length = np.mean(episode_lengths)

            self.last_mean_reward = mean_reward

            # Log results
            print(f"\nEval num_timesteps={self.num_timesteps}, episode_reward={mean_reward:.2f} +/- {std_reward:.2f}")
            print(f"  Episode length: {mean_length:.1f}")

            self.logger.record("eval/mean_reward", mean_reward)
            self.logger.record("eval/std_reward", std_reward)
            self.logger.record("eval/mean_ep_length", mean_length)

            # Save best model
            if mean_reward > self.best_mean_reward and self.best_model_save_path is not None:
                self.best_mean_reward = mean_reward
                save_path = os.path.join(self.best_model_save_path, "best_model")
                self.model.save(save_path)
                print(f"  New best model saved to {save_path}")

        return True


def make_env(rank: int, config: RLConfig):
    """
    Create a Tarot environment (for vectorized training).

    Args:
        rank: Unique ID for this environment
        config: RL configuration

    Returns:
        Callable that returns a monitored environment
    """

    def _init():
        env = TarotSingleAgentEnv(
            opponent_strategy=config.opponent_strategy,
            reward_mode=config.reward_mode,
        )
        # Wrap in Monitor for logging
        env = Monitor(env)
        return env

    return _init


def train(
    config: RLConfig,
    resume_from: str | None = None,
    use_multiprocessing: bool = True,
):
    """
    Train a MaskablePPO agent on the Tarot environment.

    Args:
        config: Training configuration
        resume_from: Path to checkpoint to resume from
        use_multiprocessing: Use SubprocVecEnv (True) or DummyVecEnv (False)
    """
    print("=" * 60)
    print("Training Tarot RL Agent with MaskablePPO")
    print("=" * 60)
    print(f"Opponent strategy: {config.opponent_strategy}")
    print(f"Reward mode: {config.reward_mode}")
    print(f"Number of environments: {config.n_envs}")
    print(f"Total timesteps: {config.total_timesteps:,}")
    print(f"Learning rate: {config.learning_rate}")
    print("=" * 60)

    # Create vectorized environments
    if use_multiprocessing and config.n_envs > 1:
        print(f"Using SubprocVecEnv with {config.n_envs} parallel environments")
        vec_env = SubprocVecEnv([make_env(i, config) for i in range(config.n_envs)])
    else:
        print(f"Using DummyVecEnv with {config.n_envs} environments")
        vec_env = DummyVecEnv([make_env(i, config) for i in range(config.n_envs)])

    # Create evaluation environment
    eval_env = Monitor(
        TarotSingleAgentEnv(
            opponent_strategy=config.opponent_strategy,
            reward_mode=config.reward_mode,
        )
    )

    # Create callbacks
    os.makedirs(config.checkpoint_dir, exist_ok=True)

    checkpoint_callback = CheckpointCallback(
        save_freq=config.save_freq // config.n_envs,  # Divide by n_envs for per-env steps
        save_path=config.checkpoint_dir,
        name_prefix="ppo_tarot",
        save_replay_buffer=False,
        save_vecnormalize=False,
    )

    eval_callback = MaskableEvalCallback(
        eval_env,
        best_model_save_path=config.checkpoint_dir,
        log_path=config.checkpoint_dir,
        eval_freq=config.eval_freq // config.n_envs,
        n_eval_episodes=config.eval_episodes,
        deterministic=True,
    )

    # Create or load model
    if resume_from:
        print(f"\nResuming training from: {resume_from}")
        model = MaskablePPO.load(
            resume_from,
            env=vec_env,
            tensorboard_log=config.tensorboard_log,
        )
    else:
        print("\nCreating new MaskablePPO model")
        model = MaskablePPO(
            "MlpPolicy",
            vec_env,
            learning_rate=config.learning_rate,
            n_steps=config.n_steps,
            batch_size=config.batch_size,
            n_epochs=config.n_epochs,
            gamma=config.gamma,
            gae_lambda=config.gae_lambda,
            clip_range=config.clip_range,
            ent_coef=config.ent_coef,
            vf_coef=config.vf_coef,
            max_grad_norm=config.max_grad_norm,
            verbose=1,
            tensorboard_log=config.tensorboard_log,
        )

    print("\nStarting training...")
    print(f"Tensorboard logs: {config.tensorboard_log}")
    print(f"Run: tensorboard --logdir {config.tensorboard_log}")
    print()

    # Train the agent
    try:
        model.learn(
            total_timesteps=config.total_timesteps,
            callback=[checkpoint_callback, eval_callback],
            progress_bar=True,
        )
    except KeyboardInterrupt:
        print("\n\nTraining interrupted by user!")

    # Save final model
    print(f"\nSaving final model to: {config.model_save_path}")
    model.save(config.model_save_path)

    print("\nTraining complete!")
    print(f"Final model saved: {config.model_save_path}")
    print(f"Checkpoints: {config.checkpoint_dir}")

    # Cleanup
    vec_env.close()
    eval_env.close()


def main():
    """Parse arguments and run training."""
    parser = argparse.ArgumentParser(description="Train Tarot RL agent with MaskablePPO")

    parser.add_argument(
        "--opponent",
        type=str,
        default=DEFAULT_CONFIG.opponent_strategy,
        help="Opponent strategy (bot-naive, bot-random, rl-snapshot-v1, etc.)",
    )

    parser.add_argument(
        "--reward-mode",
        type=str,
        default=DEFAULT_CONFIG.reward_mode,
        choices=["sparse", "dense"],
        help="Reward mode (sparse=win/loss, dense=score-based)",
    )

    parser.add_argument(
        "--timesteps",
        type=int,
        default=DEFAULT_CONFIG.total_timesteps,
        help="Total training timesteps",
    )

    parser.add_argument(
        "--n-envs",
        type=int,
        default=DEFAULT_CONFIG.n_envs,
        help="Number of parallel environments",
    )

    parser.add_argument(
        "--learning-rate",
        type=float,
        default=DEFAULT_CONFIG.learning_rate,
        help="Learning rate",
    )

    parser.add_argument(
        "--resume",
        type=str,
        default=None,
        help="Path to checkpoint to resume from",
    )

    parser.add_argument(
        "--no-multiprocessing",
        action="store_true",
        help="Use DummyVecEnv instead of SubprocVecEnv",
    )

    parser.add_argument(
        "--tensorboard-log",
        type=str,
        default=DEFAULT_CONFIG.tensorboard_log,
        help="Tensorboard log directory",
    )

    args = parser.parse_args()

    # Create config from args
    config = RLConfig(
        opponent_strategy=args.opponent,
        reward_mode=args.reward_mode,
        total_timesteps=args.timesteps,
        n_envs=args.n_envs,
        learning_rate=args.learning_rate,
        tensorboard_log=args.tensorboard_log,
    )

    # Run training
    train(
        config=config,
        resume_from=args.resume,
        use_multiprocessing=not args.no_multiprocessing,
    )


if __name__ == "__main__":
    main()
