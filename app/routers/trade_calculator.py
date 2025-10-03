from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Dict, Any
from app.db_conn import get_conn

router = APIRouter()

# -------- Search (by name) --------
# Frontend calls this for type-ahead. It shows matching players with IDs.
@router.get("/search")
def search_players(q: str = Query(min_length=1, max_length=50), limit: int = Query(12, ge=1, le=50)):
    like = f"%{q.strip()}%"
    sql = """
      SELECT p.sleeper_id AS id,
             p.full_name   AS name,
             p.position    AS pos,
             COALESCE(p.nfl_team_code, 'FA') AS team,
             COALESCE(m.valuation, 0) AS val
      FROM players p
      LEFT JOIN player_metrics m ON m.player_id = p.sleeper_id
      WHERE p.full_name LIKE ?
      ORDER BY m.valuation DESC, p.full_name ASC
      LIMIT ?
    """
    with get_conn() as con:
        rows = con.execute(sql, (like, limit)).fetchall()
    return [
        {"id": r["id"], "name": r["name"], "pos": r["pos"], "team": r["team"], "val": float(r["val"] or 0)}
        for r in rows
    ]

# -------- Simulate (IDs only) --------
# Frontend sends the selected IDs from the search results.
class TradePayload(BaseModel):
    side_a: List[str] = []
    side_b: List[str] = []

@router.post("/simulate")
def simulate_trade(payload: TradePayload):
    # sanity: same player on both sides is invalid
    both = set(payload.side_a) & set(payload.side_b)
    if both:
        raise HTTPException(status_code=400, detail=f"Player(s) on both sides: {sorted(both)}")

    ids = list(set(payload.side_a) | set(payload.side_b))
    players_by_id: Dict[str, Dict[str, Any]] = {}
    if ids:
        qmarks = ",".join("?" for _ in ids)
        sql = f"""
          SELECT p.sleeper_id,
                 p.full_name,
                 p.position,
                 COALESCE(p.nfl_team_code, 'FA') AS team,
                 COALESCE(m.valuation, 0.0) AS valuation
          FROM players p
          LEFT JOIN player_metrics m ON m.player_id = p.sleeper_id
          WHERE p.sleeper_id IN ({qmarks})
        """
        with get_conn() as con:
            rows = con.execute(sql, ids).fetchall()
        players_by_id = {r["sleeper_id"]: dict(r) for r in rows}

    def pack(side: List[str]):
        total = 0.0
        items = []
        for pid in side:
            r = players_by_id.get(pid)
            if not r:
                # unknown ID -> keep it obvious
                items.append({"sleeper_id": pid, "full_name": None, "position": None, "team": None, "valuation": 0.0, "error": "unknown_player_id"})
                continue
            v = float(r["valuation"] or 0.0)
            total += v
            items.append({
                "sleeper_id": r["sleeper_id"],
                "full_name": r["full_name"],
                "position": r["position"],
                "team": r["team"],
                "valuation": v,
            })
        return {"total": round(total, 2), "players": items}

    side_a = pack(payload.side_a)
    side_b = pack(payload.side_b)

    delta = round(side_a["total"] - side_b["total"], 2)
    winner = "A" if delta > 0.5 else ("B" if delta < -0.5 else "even")
    bigger = max(side_a["total"], side_b["total"], 1e-9)
    margin_pct = round(abs(delta) / bigger * 100, 2)

    return {"side_a": side_a, "side_b": side_b, "delta": delta, "winner": winner, "margin_pct": margin_pct}

@router.get("/")
def index():
    return {
        "search": "/trade_calculator/search?q=NAME",
        "simulate": "/trade_calculator/simulate",
        "note": "search by name, simulate with IDs"
    }
