import sqlite3
from app.config import get_db_path

def main():
    con = sqlite3.connect(get_db_path())
    con.row_factory = sqlite3.Row

    name = "Malik Nabers"
    row = con.execute("""
        SELECT p.sleeper_id, p.full_name, p.position, p.nfl_team_code, 
               m.valuation, m.overall_rank, m.position_rank, 
               t.adds_24h, t.drops_24h
        FROM players p
        LEFT JOIN player_metrics m ON m.player_id = p.sleeper_id
        LEFT JOIN player_trending t ON t.player_id = p.sleeper_id
        WHERE p.full_name LIKE ?
    """, (f"%{name}%",)).fetchone()

    if row:
        print(dict(row))
    else:
        print(f"No player found for {name}")

    con.close()

if __name__ == "__main__":
    main()
