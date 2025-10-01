import requests
from app.ingest.utils import get_conn

ADD_URL = "https://api.sleeper.app/v1/players/nfl/trending/add"
DROP_URL = "https://api.sleeper.app/v1/players/nfl/trending/drop"

def fetch(url: str) -> dict[str, int]:
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    out = {}
    for item in r.json():
        pid = str(item.get("player_id"))
        if pid:
            out[pid] = int(item.get("count") or 0)
    return out

def main():
    adds = fetch(ADD_URL)
    drops = fetch(DROP_URL)
    all_ids = sorted(set(adds) | set(drops))
    with get_conn() as conn:
        cur = conn.cursor()
        if all_ids:
            q = ",".join("?" for _ in all_ids)
            known = {r[0] for r in cur.execute(f"SELECT sleeper_id FROM players WHERE sleeper_id IN ({q})", all_ids)}
        else:
            known = set()
        cur.execute("DELETE FROM player_trending;")
        rows = []
        for pid in all_ids:
            if pid not in known:
                continue
            rows.append((pid, int(adds.get(pid, 0)), int(drops.get(pid, 0))))
        if rows:
            cur.executemany("INSERT INTO player_trending (player_id, adds_24h, drops_24h) VALUES (?, ?, ?)", rows)
        conn.commit()
    print(f"Trending updated: {len(rows)} players")

if __name__ == "__main__":
    main()
