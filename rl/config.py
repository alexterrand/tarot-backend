"""Configuration for RL training."""

from dataclasses import dataclass


@dataclass
class RLConfig:
    """RL training hyperparameters for Stable-Baselines3."""

    # State representation
    state_dim: int = 506
    action_dim: int = 78

    # PPO hyperparameters (SB3 defaults work well, these are overrides if needed)
    learning_rate: float = 3e-4
    gamma: float = 0.99  # Discount factor for rewards
    gae_lambda: float = 0.95  # GAE lambda for advantage estimation
    clip_range: float = 0.2  # PPO clipping parameter
    ent_coef: float = 0.01  # Entropy coefficient (exploration)
    vf_coef: float = 0.5  # Value function coefficient
    max_grad_norm: float = 0.5  # Gradient clipping

    # Training schedule
    n_steps: int = 2048  # Steps per environment before update
    batch_size: int = 64  # Minibatch size
    n_epochs: int = 10  # Number of epochs per update
    total_timesteps: int = 500_000  # Total training timesteps

    # Multi-environment settings
    n_envs: int = 8  # Number of parallel environments

    # Opponent strategy
    opponent_strategy: str = "bot-naive"  # Strategy for 3 opponent bots

    # Reward design
    reward_mode: str = "sparse"  # "sparse" (+1 win, 0 loss) or "dense" (score-based)

    # Checkpointing
    checkpoint_dir: str = "models/checkpoints"
    save_freq: int = 10_000  # Save every N steps
    eval_freq: int = 10_000  # Evaluate every N steps
    eval_episodes: int = 100  # Episodes for evaluation

    # Tensorboard
    tensorboard_log: str = "./runs/"

    # Model save path
    model_save_path: str = "models/ppo_tarot_v1"

    # Curriculum learning
    curriculum_enabled: bool = False
    curriculum_milestones: list[int] = None  # Timesteps to upgrade opponents

    def __post_init__(self):
        if self.curriculum_milestones is None:
            self.curriculum_milestones = [100_000, 200_000, 300_000]


# Default config instance
DEFAULT_CONFIG = RLConfig()
