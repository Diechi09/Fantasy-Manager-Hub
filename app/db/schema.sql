PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;

CREATE TABLE IF NOT EXISTS users (
  id             INTEGER PRIMARY KEY,
  email          TEXT NOT NULL UNIQUE,
  password_hash  TEXT NOT NULL,
  created_at     INTEGER NOT NULL DEFAULT (strftime('%s','now')),
  is_active      INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS leagues (
  id             INTEGER PRIMARY KEY,
  owner_user_id  INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  name           TEXT NOT NULL,
  season         INTEGER NOT NULL,
  scoring        TEXT,
  UNIQUE(owner_user_id, name, season)
);

CREATE TABLE IF NOT EXISTS league_teams (
  id           INTEGER PRIMARY KEY,
  league_id    INTEGER NOT NULL REFERENCES leagues(id) ON DELETE CASCADE,
  display_name TEXT NOT NULL,
  UNIQUE(league_id, display_name)
);

CREATE TABLE IF NOT EXISTS players (
  sleeper_id     TEXT PRIMARY KEY,
  full_name      TEXT NOT NULL,
  first_name     TEXT,
  last_name      TEXT,
  position       TEXT NOT NULL,
  nfl_team_code  TEXT,
  age            INTEGER,
  status         TEXT,
  years_exp      INTEGER,
  height         TEXT,
  weight         TEXT,
  college        TEXT
);

CREATE INDEX IF NOT EXISTS idx_players_name ON players(full_name);
CREATE INDEX IF NOT EXISTS idx_players_pos ON players(position);
CREATE INDEX IF NOT EXISTS idx_players_team ON players(nfl_team_code);

CREATE TABLE IF NOT EXISTS roster_entries (
  id              INTEGER PRIMARY KEY,
  league_team_id  INTEGER NOT NULL REFERENCES league_teams(id) ON DELETE CASCADE,
  player_id       TEXT NOT NULL REFERENCES players(sleeper_id) ON DELETE RESTRICT,
  slot            TEXT,
  UNIQUE(league_team_id, player_id)
);

CREATE INDEX IF NOT EXISTS idx_roster_entries_team ON roster_entries(league_team_id);
CREATE INDEX IF NOT EXISTS idx_roster_entries_player ON roster_entries(player_id);

CREATE TABLE IF NOT EXISTS player_metrics (
  player_id     TEXT PRIMARY KEY REFERENCES players(sleeper_id) ON DELETE CASCADE,
  valuation     REAL NOT NULL,
  overall_rank  INTEGER,
  position_rank INTEGER,
  trend_30d     REAL
);

CREATE INDEX IF NOT EXISTS idx_metrics_overall ON player_metrics(overall_rank);
CREATE INDEX IF NOT EXISTS idx_metrics_pos_rank ON player_metrics(position_rank);

CREATE TABLE IF NOT EXISTS player_trending (
  player_id  TEXT PRIMARY KEY REFERENCES players(sleeper_id) ON DELETE CASCADE,
  adds_24h   INTEGER NOT NULL DEFAULT 0,
  drops_24h  INTEGER NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_trending_adds ON player_trending(adds_24h DESC);
CREATE INDEX IF NOT EXISTS idx_trending_drops ON player_trending(drops_24h DESC);
