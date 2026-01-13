# Supabase Setup

## 1. Create Project
- Project name: `tarot`
- Save database password

## 2. Run SQL Migration
- SQL Editor → Run `migrations/001_create_game_tables.sql`
- Verify 4 tables created: `games`, `game_rounds`, `tricks`, `bot_decisions`

## 3. Get Credentials
- Project Settings → API
- Copy: **Project URL** + **service_role key** (NOT anon key)

## 4. Configure Backend
```env
# backend/.env
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_KEY=eyJhbG...  # service_role key
```

## 5. Install Dependency
```bash
cd backend && uv add supabase
```

## Schema
```
games → game_rounds → tricks → bot_decisions
```

## Card Format
`"(suit_code,rank_value)"` - e.g., `"(co,14)"` = King of Hearts

Suit codes: `co`=Hearts, `pi`=Spades, `ca`=Diamonds, `tr`=Clubs, `at`=Trump, `ex`=Excuse
