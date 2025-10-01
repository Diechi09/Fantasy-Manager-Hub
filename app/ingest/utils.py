import sqlite3
from contextlib import contextmanager
from app.config import get_db_path

@contextmanager
def get_conn():
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode = WAL;")
    try:
        yield conn
    finally:
        conn.close()

def upsert_player(conn, p: dict):
    first = (p.get("first_name") or "").strip()
    last = (p.get("last_name") or "").strip()
    full = (first + " " + last).strip() or p.get("search_full_name") or p.get("full_name") or ""
    position = p.get("position") or (p.get("fantasy_positions") or [None])[0]
    conn.execute("""
        INSERT INTO players (sleeper_id, full_name, first_name, last_name, position, nfl_team_code, age, status, years_exp, height, weight, college)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(sleeper_id) DO UPDATE SET
          full_name=excluded.full_name,
          first_name=excluded.first_name,
          last_name=excluded.last_name,
          position=excluded.position,
          nfl_team_code=excluded.nfl_team_code,
          age=excluded.age,
          status=excluded.status,
          years_exp=excluded.years_exp,
          height=excluded.height,
          weight=excluded.weight,
          college=excluded.college
    """, (
        p.get("player_id"),
        full,
        first or None,
        last or None,
        position,
        p.get("team"),
        p.get("age"),
        p.get("status"),
        p.get("years_exp"),
        p.get("height"),
        p.get("weight"),
        p.get("college"),
    ))
