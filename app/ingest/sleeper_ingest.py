import requests
from app.ingest.utils import get_conn, upsert_player

URL = "https://api.sleeper.app/v1/players/nfl"

def main():
    r = requests.get(URL, timeout=60)
    r.raise_for_status()
    data = r.json()
    inserted = updated = 0
    with get_conn() as conn:
        cur = conn.cursor()
        for sid, p in data.items():
            if p.get("sport") != "nfl":
                continue
            if not p.get("position") and not p.get("fantasy_positions"):
                continue
            p["player_id"] = sid
            exists = cur.execute("SELECT 1 FROM players WHERE sleeper_id = ?;", (sid,)).fetchone()
            upsert_player(conn, p)
            inserted += 0 if exists else 1
            updated  += 1 if exists else 0
        conn.commit()
    print(f"Players → inserted: {inserted}, updated: {updated}")

if __name__ == "__main__":
    main()
