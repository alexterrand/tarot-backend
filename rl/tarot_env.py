"""Gymnasium environment for Tarot card game with single RL agent vs 3 bots."""

import gymnasium as gym
import numpy as np
from typing import Optional, Dict, Any

from tarot_logic.deck import Deck
from tarot_logic.game_state import GameState
from tarot_logic.card import Card
from tarot_logic.rules import get_legal_moves
from tarot_logic.bots import create_strategy, create_bidding_strategy, create_dog_discard_strategy
from tarot_logic.bidding_phase import run_bidding_phase, run_dog_phase, finalize_contract
from rl.state_encoder import StateEncoder


class TarotSingleAgentEnv(gym.Env):
    """
    Gymnasium environment where 1 RL agent plays against 3 fixed bots.

    The RL agent is always player_0.
    The 3 opponents (player_1, player_2, player_3) use the specified bot strategy.

    Observation space: Box(506,) - Encoded game state
    Action space: Discrete(78) - Card index to play (must be legal)
    """

    metadata = {"render_modes": []}

    def __init__(
        self,
        opponent_strategy: str = "bot-naive",
        reward_mode: str = "sparse",
        verbose: bool = False,
    ):
        """
        Initialize the Tarot environment.

        Args:
            opponent_strategy: Strategy name for the 3 opponent bots
            reward_mode: "sparse" (win/loss only) or "dense" (score-based)
            verbose: Print game results (for debugging)
        """
        super().__init__()

        # Environment configuration
        self.opponent_strategy = opponent_strategy
        self.reward_mode = reward_mode
        self.verbose = verbose

        # RL agent is always player 0
        self.rl_agent_index = 0
        self.num_players = 4

        # Create opponent bots
        self.opponent_bots = [
            create_strategy(opponent_strategy) for _ in range(3)
        ]

        # Bidding and dog strategies (for all players including RL agent)
        self.bidding_strategy = create_bidding_strategy("point-based")
        self.dog_strategy = create_dog_discard_strategy("max-points")

        # State encoder
        self.encoder = StateEncoder()

        # Gym spaces
        self.observation_space = gym.spaces.Box(
            low=0.0,
            high=1.0,
            shape=(self.encoder.get_state_dim(),),
            dtype=np.float32
        )

        self.action_space = gym.spaces.Discrete(78)

        # Game state
        self.game_state: Optional[GameState] = None
        self.player_ids = [f"player_{i}" for i in range(self.num_players)]

        # Track if game is over
        self._terminated = False
        self._truncated = False

    def reset(
        self,
        seed: Optional[int] = None,
        options: Optional[Dict[str, Any]] = None
    ) -> tuple[np.ndarray, Dict[str, Any]]:
        """
        Reset the environment and start a new game.

        Returns:
            Initial observation and info dict
        """
        super().reset(seed=seed)

        # Create new game
        self.game_state = GameState(self.player_ids)

        # Deal cards
        deck = Deck()
        deck.shuffle()
        hands, dog = deck.deal(self.num_players)

        # Distribute cards
        for i, player in enumerate(self.game_state.players):
            player.hand = hands[i]

        self.game_state.dog = dog

        # === BIDDING PHASE ===
        bidding_strategies = {
            player_id: self.bidding_strategy for player_id in self.player_ids
        }

        someone_took = run_bidding_phase(self.game_state, bidding_strategies)

        if not someone_took:
            # All passed - restart game
            return self.reset(seed=seed, options=options)

        # === DOG PHASE ===
        taker_id = self.game_state.bidding_round.taker_id
        taker_index = self.player_ids.index(taker_id)

        run_dog_phase(self.game_state, taker_id, self.dog_strategy)
        finalize_contract(self.game_state)

        # === PLAYING PHASE ===
        # Play bot turns until it's RL agent's turn
        self._play_until_rl_turn()

        # Get initial observation
        obs = self._get_observation()
        info = self._get_info()

        self._terminated = False
        self._truncated = False

        return obs, info

    def step(self, action: int) -> tuple[np.ndarray, float, bool, bool, Dict[str, Any]]:
        """
        Execute action (play a card) and advance the game.

        Args:
            action: Card index (0-77) to play

        Returns:
            observation, reward, terminated, truncated, info
        """
        if self._terminated or self._truncated:
            raise RuntimeError("Episode is done, call reset()")

        # Decode action to card
        card = self.encoder.card_encoder.decode_card_index(action)

        # Verify action is legal
        legal_moves = self._get_legal_moves_for_rl_agent()
        if card not in legal_moves:
            # Invalid action - penalize and terminate
            obs = self._get_observation()
            reward = -1.0  # Penalty for invalid move
            self._terminated = True
            info = self._get_info()
            info["invalid_action"] = True
            return obs, reward, True, False, info

        # Play the card
        self.game_state.play_card(self.rl_agent_index, card)

        # Check if game is over
        if self.game_state.is_game_over():
            obs = self._get_observation()
            reward = self._compute_final_reward()
            self._terminated = True
            info = self._get_info()
            return obs, reward, True, False, info

        # Play opponent turns until RL agent's turn
        self._play_until_rl_turn()

        # Check again if game ended during bot turns
        if self.game_state.is_game_over():
            obs = self._get_observation()
            reward = self._compute_final_reward()
            self._terminated = True
            info = self._get_info()
            return obs, reward, True, False, info

        # Game continues
        obs = self._get_observation()
        reward = 0.0  # Sparse reward (only at end)
        info = self._get_info()

        return obs, reward, False, False, info

    def _play_until_rl_turn(self) -> None:
        """Play bot turns until it's the RL agent's turn."""
        while (
            not self.game_state.is_game_over()
            and self.game_state.current_player_index != self.rl_agent_index
        ):
            current_player_idx = self.game_state.current_player_index
            bot = self.opponent_bots[current_player_idx - 1]  # Bots are players 1, 2, 3

            player = self.game_state.players[current_player_idx]
            legal_moves = get_legal_moves(player.hand, self.game_state.current_trick)

            # Import Trick for bot decision
            from tarot_logic.trick import Trick
            current_trick_obj = Trick()
            current_trick_obj.starter_index = self.game_state.trick_starter_index
            current_trick_obj.cards = self.game_state.current_trick.copy()
            current_trick_obj.player_indices = self.game_state.trick_player_indices.copy()

            bot_card = bot.choose_card(player.hand, legal_moves, current_trick_obj)
            self.game_state.play_card(current_player_idx, bot_card)

    def _get_observation(self) -> np.ndarray:
        """Encode current game state for RL agent."""
        player = self.game_state.players[self.rl_agent_index]
        legal_moves = self._get_legal_moves_for_rl_agent()

        # Create Trick object for encoding
        from tarot_logic.trick import Trick
        current_trick_obj = Trick()
        current_trick_obj.starter_index = self.game_state.trick_starter_index
        current_trick_obj.cards = self.game_state.current_trick.copy()
        current_trick_obj.player_indices = self.game_state.trick_player_indices.copy()

        # Compute position in trick
        position_in_trick = len(self.game_state.current_trick)

        # Check if RL agent is taker
        is_taker = (
            self.game_state.contract is not None
            and self.game_state.contract.taker_id == self.player_ids[self.rl_agent_index]
        )

        # Compute trick number
        total_cards_played = sum(len(p.tricks_won) * self.num_players for p in self.game_state.players)
        total_cards_played += len(self.game_state.current_trick)
        trick_number = (total_cards_played // self.num_players) + 1

        return self.encoder.encode_state(
            hand=player.hand,
            legal_moves=legal_moves,
            current_trick=current_trick_obj,
            position_in_trick=position_in_trick,
            is_taker=is_taker,
            contract=self.game_state.contract,
            trick_number=trick_number,
            total_tricks=78 // self.num_players,
        )

    def _get_legal_moves_for_rl_agent(self) -> list[Card]:
        """Get legal moves for the RL agent."""
        player = self.game_state.players[self.rl_agent_index]
        return get_legal_moves(player.hand, self.game_state.current_trick)

    def action_masks(self) -> np.ndarray:
        """
        Return action mask for MaskablePPO.

        Returns:
            np.ndarray of shape (78,) with 1 for legal actions, 0 for illegal
        """
        legal_moves = self._get_legal_moves_for_rl_agent()
        mask = np.zeros(78, dtype=np.int8)

        for card in legal_moves:
            card_idx = self.encoder.card_encoder.get_card_index(card)
            mask[card_idx] = 1

        return mask

    def _compute_final_reward(self) -> float:
        """Compute reward based on game outcome."""
        if self.game_state.contract is None:
            return 0.0  # Abandoned game

        is_taker = (
            self.game_state.contract.taker_id == self.player_ids[self.rl_agent_index]
        )

        # Compute taker points
        taker_id = self.game_state.contract.taker_id
        taker_index = self.player_ids.index(taker_id)
        taker_player = self.game_state.players[taker_index]

        # Collect all taker cards (tricks + dog)
        taker_cards = []
        for trick in taker_player.tricks_won:
            taker_cards.extend(trick)
        taker_cards.extend(self.game_state.dog)

        # Calculate taker points
        taker_points = sum(card.get_points() for card in taker_cards)

        # Defense points (total - taker)
        defense_points = 91 - taker_points

        # Compute final scores
        from tarot_logic.scoring import calculate_player_scores
        final_scores = calculate_player_scores(
            self.game_state.contract,
            taker_points,
            self.player_ids,
            self.num_players
        )

        # Log game result if verbose
        if self.verbose:
            rl_agent_score = final_scores[self.player_ids[self.rl_agent_index]]
            taker_won = taker_points >= self.game_state.contract.points_needed
            print(f"\n[GAME END] Taker: {taker_id} ({'RL' if is_taker else 'Bot'})")
            print(f"  Taker points: {taker_points:.1f} / {self.game_state.contract.points_needed} {'✓ WIN' if taker_won else '✗ LOSS'}")
            print(f"  Defense points: {defense_points:.1f}")
            print(f"  RL Agent ({'Taker' if is_taker else 'Defense'}): Score={rl_agent_score:+.1f}, Reward={1.0 if rl_agent_score > 0 else 0.0}")

        if self.reward_mode == "sparse":
            # Binary reward: +1 for win, 0 for loss
            rl_agent_score = final_scores[self.player_ids[self.rl_agent_index]]
            return 1.0 if rl_agent_score > 0 else 0.0

        elif self.reward_mode == "dense":
            # Score-based reward (normalized)
            rl_agent_score = final_scores[self.player_ids[self.rl_agent_index]]
            return rl_agent_score / 100.0  # Normalize to ~[-1, 1]

        else:
            raise ValueError(f"Unknown reward mode: {self.reward_mode}")

    def _get_info(self) -> Dict[str, Any]:
        """Get info dictionary."""
        info = {
            "current_player": self.game_state.current_player_index,
            "trick_number": len(self.game_state.players[0].tricks_won),
            "is_game_over": self.game_state.is_game_over(),
        }

        if self.game_state.contract:
            info["is_taker"] = (
                self.game_state.contract.taker_id == self.player_ids[self.rl_agent_index]
            )

        return info

    def render(self):
        """Rendering not implemented."""
        pass

    def close(self):
        """Clean up resources."""
        pass
