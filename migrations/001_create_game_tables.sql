-- Supabase Migration: Create game logging tables
-- Run this script in the Supabase SQL editor to create all necessary tables

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================================
-- 1. GAMES TABLE
-- ============================================================================
-- Stores top-level game information and leaderboard across rounds

CREATE TABLE IF NOT EXISTS games (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    created_at TIMESTAMP DEFAULT NOW(),

    -- Players
    player_ids JSONB NOT NULL,  -- ["IA1", "IA2", "IA3", "IA4"]
    num_players INT NOT NULL CHECK (num_players IN (3, 4, 5)),

    -- Leaderboard (cumulative scores across rounds)
    leaderboard JSONB NOT NULL,  -- {"IA1": 120, "IA2": -45, ...}

    -- Metadata
    game_mode TEXT DEFAULT 'standard'
);

-- ============================================================================
-- 2. GAME ROUNDS TABLE
-- ============================================================================
-- Stores individual round/contract information
-- Multiple rounds can belong to one game

CREATE TABLE IF NOT EXISTS game_rounds (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    game_id UUID REFERENCES games(id) ON DELETE CASCADE,
    round_number INT NOT NULL,

    -- Contract info
    taker_id TEXT NOT NULL,
    contract_type TEXT NOT NULL CHECK (
        contract_type IN ('petite', 'garde', 'garde_sans', 'garde_contre')
    ),

    -- For 5-player variant (V5)
    called_player_id TEXT,  -- Player called by taker (King call rule)

    -- Dog/Chien composition
    dog_cards JSONB NOT NULL,  -- ["(co,5)", "(pi,12)", ...]

    -- Initial hands for all players
    initial_hands JSONB NOT NULL,  -- {"IA1": ["(co,1)", ...], "IA2": [...], ...}

    -- Hand strength metrics (for analysis)
    hand_strengths JSONB NOT NULL,  -- {"IA1": 45.5, "IA2": 38.0, ...}

    -- Contract threshold (depends on oudlers kept by taker)
    contract_points_needed INT NOT NULL CHECK (
        contract_points_needed IN (36, 41, 51, 56)
    ),

    -- Results (updated at round end)
    taker_team_points FLOAT NOT NULL DEFAULT 0,
    defense_team_points FLOAT NOT NULL DEFAULT 0,
    contract_won BOOLEAN NOT NULL DEFAULT FALSE,

    UNIQUE(game_id, round_number)
);

-- ============================================================================
-- 3. TRICKS TABLE
-- ============================================================================
-- Stores individual trick data for each round
-- Number of tricks depends on num_players: 3→24, 4→18, 5→15

CREATE TABLE IF NOT EXISTS tricks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    game_round_id UUID REFERENCES game_rounds(id) ON DELETE CASCADE,
    trick_number INT NOT NULL,

    -- Trick data
    cards_played JSONB NOT NULL,  -- [{"player": "IA1", "card": "(co,1)", "position": 0}, ...]
    winner_player_id TEXT NOT NULL,
    trick_points FLOAT NOT NULL,

    UNIQUE(game_round_id, trick_number)
);

-- ============================================================================
-- 4. BOT DECISIONS TABLE
-- ============================================================================
-- Stores bot decision data for RL training (V6)
-- One decision per player per trick

CREATE TABLE IF NOT EXISTS bot_decisions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    trick_id UUID REFERENCES tricks(id) ON DELETE CASCADE,
    player_id TEXT NOT NULL,
    strategy_name TEXT NOT NULL,

    -- State before decision (RL observation)
    hand_before JSONB NOT NULL,         -- ["(co,1)", "(co,5)", ...]
    legal_moves JSONB NOT NULL,         -- ["(co,1)", "(co,5)", ...]
    trick_state_before JSONB NOT NULL,  -- Cards already in trick
    position_in_trick INT NOT NULL,     -- 0 to num_players-1

    -- Action taken
    card_played TEXT NOT NULL,  -- "(co,1)"

    -- Game context (for V6 RL)
    is_taker BOOLEAN NOT NULL,
    contract_type TEXT NOT NULL,

    UNIQUE(trick_id, player_id)
);

-- ============================================================================
-- INDEXES FOR PERFORMANCE
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_game_rounds_game_id ON game_rounds(game_id);
CREATE INDEX IF NOT EXISTS idx_tricks_game_round_id ON tricks(game_round_id);
CREATE INDEX IF NOT EXISTS idx_bot_decisions_trick_id ON bot_decisions(trick_id);
CREATE INDEX IF NOT EXISTS idx_bot_decisions_strategy ON bot_decisions(strategy_name);

-- ============================================================================
-- COMMENTS FOR DOCUMENTATION
-- ============================================================================

COMMENT ON TABLE games IS 'Top-level game information with leaderboard';
COMMENT ON TABLE game_rounds IS 'Individual rounds/contracts within a game';
COMMENT ON TABLE tricks IS 'Individual tricks played in each round';
COMMENT ON TABLE bot_decisions IS 'Bot decision data for RL training (V6)';

COMMENT ON COLUMN game_rounds.dog_cards IS 'Size depends on num_players: 3→6, 4→6, 5→3';
COMMENT ON COLUMN tricks.trick_number IS 'Depends on num_players: 3→24, 4→18, 5→15';
COMMENT ON COLUMN bot_decisions.hand_before IS 'Cards in hand before this decision (RL state)';
COMMENT ON COLUMN bot_decisions.legal_moves IS 'Legal cards for this decision (RL action space)';
