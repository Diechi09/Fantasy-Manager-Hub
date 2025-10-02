from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Tuple
from app.db_conn import get_conn

router = APIRouter()

class TradeInput(BaseModel):
    side_a: List[str] = Field(default=[], description="Names or Sleeper IDs for Side A")
    side_b: List[str] = Field(default=[], description="Names or Sleeper IDs for Side B")

class TradePayload(BaseModel):
    side_a: List[str] = Field(default=[], description="Sleeper IDs or names for Side A")
    side_b: List[str] = Field(default=[], description="Sleeper IDs or names for Side B")


def search_players(con, q: str, limit: int = 20):
    like = f"%{q.strip()}%"
    rows = con.execute(
        """
        SELECT p.sleeper_id AS id,
               p.full_name   AS name,
               p.position    AS pos,
               COALESCE(p.nfl_team_code,'FA') AS team,
               COALESCE(m.valuation,0) AS val
        FROM players p
        LEFT JOIN player_metrics m ON m.player_id = p.sleeper_id
        WHERE p.full_name LIKE ?
        ORDER BY m.valuation DESC, p.full_name ASC
        LIMIT ?
        """,
        (like, limit),
    ).fetchall()
    return [dict(r) | {"val": float(r["val"] or 0)} for r in rows]

def fetch_players_by_ids(con, ids: List[str]) -> Dict[str, Dict[str, Any]]:
    if not ids:
        return {}
    qmarks = ",".join("?" for _ in ids)
    rows = con.execute(
        f"""
        SELECT p.sleeper_id,
               p.full_name,
               p.position,
               COALESCE(p.nfl_team_code,'FA') AS team,
               COALESCE(m.valuation, 0.0) AS valuation
        FROM players p
        LEFT JOIN player_metrics m ON m.player_id = p.sleeper_id
        WHERE p.sleeper_id IN ({qmarks})
        """,
        ids,
    ).fetchall()
    return {r["sleeper_id"]: dict(r) for r in rows}

def try_exact_id(con, token: str) -> str | None:
    row = con.execute("SELECT sleeper_id FROM players WHERE sleeper_id = ?", (token,)).fetchone()
    return row["sleeper_id"] if row else None

def try_exact_name(con, token: str) -> str | None:
    # exact, case-insensitive match on full name
    row = con.execute(
        "SELECT sleeper_id FROM players WHERE lower(full_name) = lower(?)",
        (token.strip(),),
    ).fetchone()
    return row["sleeper_id"] if row else None

def fuzzy_candidates(con, token: str, limit: int = 8) -> List[Dict[str, Any]]:
    return search_players(con, token, limit=limit)

def resolve_tokens(con, tokens: List[str]) -> Tuple[List[str], List[Dict[str, Any]]]:
    """
    Resolve a list of name/ID tokens to Sleeper IDs.
    Returns (resolved_ids_in_order, unresolved_info_list).
    unresolved_info_list contains { "input": str, "candidates": [...] }
    """
    resolved: List[str] = []
    unresolved: List[Dict[str, Any]] = []

    for t in tokens:
        t = (t or "").strip()
        if not t:
            continue

        # 1) Exact ID?
        sid = try_exact_id(con, t)
        if sid:
            resolved.append(sid)
            continue

        # 2) Exact name?
        sid = try_exact_name(con, t)
        if sid:
            resolved.append(sid)
            continue

        # 3) Fuzzy search
        cands = fuzzy_candidates(con, t)
        if len(cands) == 1:
            resolved.append(cands[0]["id"])
        elif len(cands) > 1:
            unresolved.append({"input": t, "candidates": cands})
        else:
            unresolved.append({"input": t, "candidates": []})

    return resolved, unresolved

def pack_side(players_by_id: Dict[str, Dict[str, Any]], ids: List[str]) -> Dict[str, Any]:
    total = 0.0
    items = []
    for pid in ids:
        rec = players_by_id.get(pid)
        if rec:
            v = float(rec.get("valuation") or 0.0)
            total += v
            items.append({
                "sleeper_id": rec["sleeper_id"],
                "full_name": rec["full_name"],
                "position": rec["position"],
                "team": rec["team"],
                "valuation": v
            })
        else:
            items.append({
                "sleeper_id": pid,
                "full_name": None,
                "position": None,
                "team": None,
                "valuation": 0.0,
                "error": "unknown_player_id"
            })
    return {"total": round(total, 2), "players": items}

# --------- Endpoints ---------

@router.get("/search")
def search(q: str = Query(default="", max_length=50), limit: int = Query(default=12, ge=1, le=50)):
    # For type-ahead; returns compact results
    with get_conn() as con:
        return search_players(con, q, limit=limit)

@router.post("/resolve")
def resolve_names(payload: TradeInput):
    with get_conn() as con:
        a_ids, a_unres = resolve_tokens(con, payload.side_a)
        b_ids, b_unres = resolve_tokens(con, payload.side_b)

    return {
        "side_a_ids": a_ids,
        "side_b_ids": b_ids,
        "unresolved": a_unres + b_unres
    }

@router.post("/simulate")
def simulate_trade(payload: TradePayload):
    """
    Accepts a mix of names and IDs. Resolves names -> IDs.
    Fails with 422 if any unresolved/ambiguous tokens remain.
    """
    with get_conn() as con:
        a_ids, a_unres = resolve_tokens(con, payload.side_a)
        b_ids, b_unres = resolve_tokens(con, payload.side_b)

        # error if unresolved
        unresolved = a_unres + b_unres
        if unresolved:
            # return precise error so the frontend can offer the candidates
            raise HTTPException(status_code=422, detail={
                "message": "Some inputs are ambiguous or unmatched.",
                "unresolved": unresolved
            })

        # no duplicates across sides
        both = set(a_ids) & set(b_ids)
        if both:
            raise HTTPException(status_code=400, detail=f"Player(s) on both sides: {sorted(both)}")

        players_by_id = fetch_players_by_ids(con, list(set(a_ids) | set(b_ids)))

    side_a = pack_side(players_by_id, a_ids)
    side_b = pack_side(players_by_id, b_ids)

    delta = round(side_a["total"] - side_b["total"], 2)
    winner = "A" if delta > 0.5 else ("B" if delta < -0.5 else "even")
    bigger = max(side_a["total"], side_b["total"], 1e-9)
    margin_pct = round(abs(delta) / bigger * 100, 2)

    return {
        "side_a": side_a,
        "side_b": side_b,
        "delta": delta,
        "winner": winner,
        "margin_pct": margin_pct
    }
