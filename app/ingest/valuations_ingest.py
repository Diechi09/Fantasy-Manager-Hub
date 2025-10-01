import pandas as pd
from pathlib import Path
from app.ingest.utils import get_conn

def main():
    # Default file: fantasycalc_redraft_rankings.csv inside this folder
    csv_file = Path(__file__).with_name("fantasycalc_redraft_rankings.csv")

    if not csv_file.exists():
        raise FileNotFoundError(f"CSV file not found: {csv_file}")

    df = pd.read_csv(csv_file, sep=";")
    # Expect columns:
    # name;team;position;age;fantasycalcId;sleeperId;mflId;value;overallRank;positionRank;trend30day

    df = df[df["sleeperId"].notna()].copy()
    df["sleeperId"] = df["sleeperId"].astype(str)

    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM player_metrics;")

        rows = []
        for _, r in df.iterrows():
            rows.append((
                r["sleeperId"],
                float(r["value"]) if pd.notna(r["value"]) else 0.0,
                int(r["overallRank"]) if pd.notna(r["overallRank"]) else None,
                int(r["positionRank"]) if pd.notna(r["positionRank"]) else None,
                float(r["trend30day"]) if pd.notna(r["trend30day"]) else None,
            ))

        cur.executemany("""
            INSERT INTO player_metrics (player_id, valuation, overall_rank, position_rank, trend_30d)
            VALUES (?, ?, ?, ?, ?)
        """, rows)

        conn.commit()

    print(f"Valuations loaded: {len(rows)} from {csv_file.name}")

if __name__ == "__main__":
    main()
