# app/routers/player_trends.py
from fastapi import APIRouter, Query
from typing import List, Optional, Tuple
from app.db_conn import get_conn

router = APIRouter()

# Non-rank sort keys map straight to SQL columns in the subquery "s"
NON_RANK_SORT_MAP = {
    "name": "s.name",
    "position": "s.position",
    "team": "s.team",
    "age": "s.age",
    "valuation": "s.valuation",
    "trend30": "s.trend30",
    "adds_24h": "s.adds_24h",
    "drops_24h": "s.drops_24h",
}

# Rank keys are computed from valuation with window functions
RANK_SORT_MAP = {
    "overall_rank": "s.overall_rank_calc",     # 1 = highest valuation overall
    "position_rank": "s.position_rank_calc",   # 1 = highest valuation within position
}


def _build_filters(
    q: Optional[str],
    positions: Optional[List[str]],
    team: Optional[str],
    min_val: Optional[float],
    max_val: Optional[float],
) -> Tuple[str, list]:
    where = []
    params: list = []

    if q:
        where.append("p.full_name LIKE ?")
        params.append(f"%{q.strip()}%")

    if positions:
        pos = [p.strip().upper() for p in positions if p.strip()]
        if pos:
            where.append("p.position IN (" + ",".join("?" for _ in pos) + ")")
            params.extend(pos)

    if team:
        where.append("p.nfl_team_code = ?")
        params.append(team.strip().upper())

    if min_val is not None:
        where.append("COALESCE(m.valuation, 0) >= ?")
        params.append(min_val)

    if max_val is not None:
        where.append("COALESCE(m.valuation, 0) <= ?")
        params.append(max_val)

    return (f"WHERE {' AND '.join(where)}" if where else ""), params


@router.get("/players")
def list_players(
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=200),
    q: Optional[str] = None,
    positions: Optional[str] = None,
    team: Optional[str] = None,
    min_val: Optional[float] = None,
    max_val: Optional[float] = None,
    sort_by: str = "valuation",
    order: str = "desc",
):
    # Parse CSV positions
    pos_list = [s for s in (positions.split(",") if positions else []) if s]

    # Normalize order
    order = (order or "desc").lower()
    if order not in ("asc", "desc"):
        order = "desc"
    order_sql = "ASC" if order == "asc" else "DESC"

    # Build filters for both COUNT and subquery
    where_sql, params = _build_filters(q, pos_list, team, min_val, max_val)
    offset = (page - 1) * page_size

    # Subquery computes ranks from valuation using window functions
    subquery = f"""
      SELECT
        p.sleeper_id AS id,
        p.full_name  AS name,
        p.position   AS position,
        COALESCE(p.nfl_team_code, 'FA') AS team,
        p.age        AS age,
        COALESCE(m.valuation, 0) AS valuation,
        DENSE_RANK() OVER (ORDER BY COALESCE(m.valuation, 0) DESC)
          AS overall_rank_calc,
        DENSE_RANK() OVER (
          PARTITION BY p.position
          ORDER BY COALESCE(m.valuation, 0) DESC
        ) AS position_rank_calc,
        (COALESCE(t.adds_24h, 0) - COALESCE(t.drops_24h, 0)) AS trend30,
        COALESCE(t.adds_24h, 0)  AS adds_24h,
        COALESCE(t.drops_24h, 0) AS drops_24h
      FROM players p
      LEFT JOIN player_metrics  m ON m.player_id = p.sleeper_id
      LEFT JOIN player_trending t ON t.player_id = p.sleeper_id
      {where_sql}
    """

    # Choose ORDER BY column
    if sort_by in RANK_SORT_MAP:
        # ranks: typically show best first, i.e. ASC
        sort_col = RANK_SORT_MAP[sort_by]
        # If the UI sends desc for a rank, we still respect it;
        # just note that "best first" = ASC.
    else:
        sort_col = NON_RANK_SORT_MAP.get(sort_by, "s.valuation")

    with get_conn() as con:
        total = con.execute(
            f"SELECT COUNT(*) FROM players p "
            f"LEFT JOIN player_metrics m ON m.player_id = p.sleeper_id "
            f"LEFT JOIN player_trending t ON t.player_id = p.sleeper_id "
            f"{where_sql}",
            params,
        ).fetchone()[0]

        rows = con.execute(
            f"""
            SELECT *
            FROM ({subquery}) AS s
            ORDER BY {sort_col} {order_sql}, s.name ASC
            LIMIT ? OFFSET ?
            """,
            (*params, page_size, offset),
        ).fetchall()

    items = [
        {
            "id": r["id"],
            "name": r["name"],
            "position": r["position"],
            "team": r["team"],
            "age": r["age"],
            "valuation": float(r["valuation"] or 0),
            "overall_rank": r["overall_rank_calc"],
            "position_rank": r["position_rank_calc"],
            "trend30": r["trend30"],
            "adds_24h": int(r["adds_24h"] or 0),
            "drops_24h": int(r["drops_24h"] or 0),
        }
        for r in rows
    ]

    return {
        "page": page,
        "page_size": page_size,
        "total": total,
        "total_pages": (total + page_size - 1) // page_size,
        "sort_by": sort_by,
        "order": order,
        "filters": {
            "q": q,
            "positions": pos_list or None,
            "team": team,
            "min_val": min_val,
            "max_val": max_val,
        },
        "items": items,
    }


@router.get("/positions")
def list_positions():
    with get_conn() as con:
        rows = con.execute(
            """
            SELECT UPPER(position) AS position, COUNT(*) AS cnt
            FROM players
            GROUP BY UPPER(position)
            ORDER BY cnt DESC
            """
        ).fetchall()
    return [{"position": r["position"], "count": r["cnt"]} for r in rows]


@router.get("/teams")
def list_teams():
    with get_conn() as con:
        rows = con.execute(
            """
            SELECT UPPER(COALESCE(nfl_team_code, 'FA')) AS team, COUNT(*) AS cnt
            FROM players
            GROUP BY team
            ORDER BY team
            """
        ).fetchall()
    return [{"team": r["team"], "count": r["cnt"]} for r in rows]
