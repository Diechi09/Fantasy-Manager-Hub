from __future__ import annotations

from typing import Dict, List, Optional, Tuple
from uuid import uuid4
from datetime import datetime

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field, conint

from app.db_conn import get_conn as db_conn

router = APIRouter()

# ---------- Pydantic models ----------

class LeagueSettings(BaseModel):
    num_teams: conint(ge=2, le=24)
    qb: conint(ge=0) = 1
    rb: conint(ge=0) = 2
    wr: conint(ge=0) = 2
    te: conint(ge=0) = 1
    flex: conint(ge=0) = 1     # generic WR/RB/TE in your UI later
    defense: conint(ge=0) = 0
    kicker: conint(ge=0) = 0
    bench: conint(ge=0) = 6

class InitSessionRequest(BaseModel):
    settings: LeagueSettings
    team_names: Optional[List[str]] = None  # optional custom names at create-time

class InitSessionResponse(BaseModel):
    session_id: str
    settings: LeagueSettings
    teams: List[Dict]

class RenameTeamRequest(BaseModel):
    name: str

class SearchResponseItem(BaseModel):
    id: int
    name: str
    position: str
    team: Optional[str] = None
    valuation: float

class AddPlayerRequest(BaseModel):
    player_id: int

class RemovePlayerRequest(BaseModel):
    player_id: int

class PositionSummary(BaseModel):
    position: str
    count: int
    value: float
    z_score: Optional[float] = None
    rank: Optional[int] = None

class TeamAnalysis(BaseModel):
    team_id: int
    team_name: str
    total_value: float
    by_position: List[PositionSummary]

class SessionAnalysis(BaseModel):
    session_id: str
    teams: List[TeamAnalysis]


# ---------- Table bootstrap (idempotent) ----------

def _ensure_tables():
    with db_conn() as con:
        con.execute("""
            CREATE TABLE IF NOT EXISTS roster_session(
                id TEXT PRIMARY KEY,
                created_at TEXT NOT NULL,
                num_teams INTEGER NOT NULL,
                qb_slots INTEGER NOT NULL,
                rb_slots INTEGER NOT NULL,
                wr_slots INTEGER NOT NULL,
                te_slots INTEGER NOT NULL,
                flex_slots INTEGER NOT NULL,
                def_slots INTEGER NOT NULL,
                k_slots INTEGER NOT NULL,
                bench_slots INTEGER NOT NULL
            )
        """)
        con.execute("""
            CREATE TABLE IF NOT EXISTS roster_team(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                name TEXT NOT NULL,
                FOREIGN KEY(session_id) REFERENCES roster_session(id)
            )
        """)
        con.execute("""
            CREATE TABLE IF NOT EXISTS roster_team_player(
                team_id INTEGER NOT NULL,
                player_id INTEGER NOT NULL,
                PRIMARY KEY(team_id, player_id),
                FOREIGN KEY(team_id) REFERENCES roster_team(id),
                FOREIGN KEY(player_id) REFERENCES players(id)
            )
        """)

_ensure_tables()


# ---------- Helpers ----------

def _settings_row_to_model(row) -> LeagueSettings:
    return LeagueSettings(
        num_teams=row["num_teams"],
        qb=row["qb_slots"],
        rb=row["rb_slots"],
        wr=row["wr_slots"],
        te=row["te_slots"],
        flex=row["flex_slots"],
        defense=row["def_slots"],
        kicker=row["k_slots"],
        bench=row["bench_slots"],
    )


def _pos_key_to_label(pos_key: str) -> str:
    return {
        "QB": "QB",
        "RB": "RB",
        "WR": "WR",
        "TE": "TE",
        "DEF": "DEF",
        "K": "K",
    }.get(pos_key, pos_key)


# ---------- Endpoints ----------

@router.post("/init", response_model=InitSessionResponse)
def init_session(payload: InitSessionRequest):
    s = payload.settings
    session_id = str(uuid4())

    with db_conn() as con:
        con.execute(
            """
            INSERT INTO roster_session(
                id, created_at, num_teams, qb_slots, rb_slots, wr_slots, te_slots,
                flex_slots, def_slots, k_slots, bench_slots
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                session_id,
                datetime.utcnow().isoformat(),
                s.num_teams, s.qb, s.rb, s.wr, s.te,
                s.flex, s.defense, s.kicker, s.bench,
            ],
        )

        team_names = payload.team_names or [f"Team {i+1}" for i in range(s.num_teams)]
        if len(team_names) != s.num_teams:
            raise HTTPException(status_code=400, detail="team_names length must match num_teams")

        teams = []
        for name in team_names:
            cur = con.execute(
                "INSERT INTO roster_team(session_id, name) VALUES(?, ?)",
                [session_id, name],
            )
            team_id = cur.lastrowid
            teams.append({"id": team_id, "name": name})

    return InitSessionResponse(session_id=session_id, settings=s, teams=teams)


@router.put("/{session_id}/team/{team_id}/rename")
def rename_team(session_id: str, team_id: int, payload: RenameTeamRequest):
    with db_conn() as con:
        cur = con.execute(
            "UPDATE roster_team SET name=? WHERE id=? AND session_id=?",
            [payload.name, team_id, session_id],
        )
        if cur.rowcount == 0:
            raise HTTPException(status_code=404, detail="Team not found")
    return {"ok": True}


@router.get("/{session_id}/search", response_model=List[SearchResponseItem])
def search_players(
    session_id: str,
    q: str = Query(..., min_length=1),
    limit: conint(ge=1, le=50) = 20,
    position: Optional[str] = Query(None, regex="^(QB|RB|WR|TE|DEF|K)$"),
):
    sql = """
        SELECT id, name, position, team, valuation
        FROM players
        WHERE name LIKE ? {pos_filter}
        ORDER BY valuation DESC
        LIMIT ?
    """
    pos_filter = ""
    params: List = [f"%{q}%", ]
    if position:
        pos_filter = "AND position = ?"
        params.append(position)
    params.append(limit)

    with db_conn() as con:
        rows = con.execute(sql.format(pos_filter=pos_filter), params).fetchall()

    return [
        SearchResponseItem(
            id=r["id"], name=r["name"], position=r["position"], team=r["team"], valuation=r["valuation"] or 0.0
        )
        for r in rows
    ]


@router.post("/{session_id}/team/{team_id}/add_player")
def add_player(session_id: str, team_id: int, payload: AddPlayerRequest):
    with db_conn() as con:
        # Ensure team exists in session
        row = con.execute(
            "SELECT 1 FROM roster_team WHERE id=? AND session_id=?",
            [team_id, session_id],
        ).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Team not found")

        # Ensure player exists
        p = con.execute("SELECT 1 FROM players WHERE id=?", [payload.player_id]).fetchone()
        if not p:
            raise HTTPException(status_code=404, detail="Player not found")

        # Insert (ignore if duplicate)
        try:
            con.execute(
                "INSERT INTO roster_team_player(team_id, player_id) VALUES(?, ?)",
                [team_id, payload.player_id],
            )
        except Exception:
            pass

    return {"ok": True}


@router.post("/{session_id}/team/{team_id}/remove_player")
def remove_player(session_id: str, team_id: int, payload: RemovePlayerRequest):
    with db_conn() as con:
        cur = con.execute(
            "DELETE FROM roster_team_player WHERE team_id=? AND player_id=?",
            [team_id, payload.player_id],
        )
        if cur.rowcount == 0:
            raise HTTPException(status_code=404, detail="Row not found")
    return {"ok": True}


@router.get("/{session_id}/analysis", response_model=SessionAnalysis)
def analyze_session(session_id: str):
    with db_conn() as con:
        sess = con.execute(
            "SELECT * FROM roster_session WHERE id=?",
            [session_id],
        ).fetchone()
        if not sess:
            raise HTTPException(status_code=404, detail="Session not found")

        teams = con.execute(
            "SELECT id, name FROM roster_team WHERE session_id=? ORDER BY id",
            [session_id],
        ).fetchall()

        # Per-team, per-position: counts + value
        # Note: valuation source = players.valuation
        per_team_pos = con.execute(
            """
            SELECT
                rtp.team_id,
                p.position AS pos,
                COUNT(*) AS cnt,
                COALESCE(SUM(COALESCE(p.valuation, 0)), 0) AS val
            FROM roster_team_player rtp
            JOIN players p ON p.id = rtp.player_id
            WHERE rtp.team_id IN (SELECT id FROM roster_team WHERE session_id = ?)
            GROUP BY rtp.team_id, p.position
            """,
            [session_id],
        ).fetchall()

        # Build lookups
        team_ids = [t["id"] for t in teams]
        pos_set = {"QB", "RB", "WR", "TE", "DEF", "K"}

        team_pos_map: Dict[int, Dict[str, Tuple[int, float]]] = {tid: {} for tid in team_ids}
        for r in per_team_pos:
            team_pos_map[r["team_id"]][r["pos"]] = (r["cnt"], float(r["val"]))

        # League stats per position (mean & std of values across teams)
        league_pos_values: Dict[str, List[float]] = {pos: [] for pos in pos_set}
        for tid in team_ids:
            for pos in pos_set:
                cnt, val = team_pos_map.get(tid, {}).get(pos, (0, 0.0))
                league_pos_values[pos].append(val)

        def mean_std(vals: List[float]) -> Tuple[float, float]:
            if not vals:
                return 0.0, 0.0
            m = sum(vals) / len(vals)
            # population std is fine here
            var = sum((v - m) ** 2 for v in vals) / len(vals)
            return m, var ** 0.5

        pos_stats: Dict[str, Tuple[float, float]] = {
            pos: mean_std(vals) for pos, vals in league_pos_values.items()
        }

        # Prepare response
        teams_out: List[TeamAnalysis] = []
        for t in teams:
            tid = t["id"]
            name = t["name"]

            by_pos: List[PositionSummary] = []
            total_value = 0.0

            # We'll also make ranks from the league lists
            for pos in sorted(pos_set):  # consistent order
                cnt, val = team_pos_map.get(tid, {}).get(pos, (0, 0.0))
                total_value += val

                mean, std = pos_stats[pos]
                z = (val - mean) / std if std > 0 else None

                # rank: 1 = best (desc on value)
                values_for_rank = league_pos_values[pos]
                rank = sorted(values_for_rank, reverse=True).index(val) + 1 if values_for_rank else None

                by_pos.append(
                    PositionSummary(
                        position=_pos_key_to_label(pos),
                        count=cnt,
                        value=round(val, 2),
                        z_score=round(z, 2) if z is not None else None,
                        rank=rank,
                    )
                )

            teams_out.append(
                TeamAnalysis(
                    team_id=tid,
                    team_name=name,
                    total_value=round(total_value, 2),
                    by_position=by_pos,
                )
            )

    return SessionAnalysis(session_id=session_id, teams=teams_out)
