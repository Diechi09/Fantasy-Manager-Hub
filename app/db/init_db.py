import sqlite3
from pathlib import Path
from app.config import get_db_path

SCHEMA_FILE = Path(__file__).with_name("schema.sql")

def main():
    db_path = Path(get_db_path())
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as conn, SCHEMA_FILE.open("r", encoding="utf-8") as f:
        conn.executescript(f.read())
    print(f"DB ready → {db_path}")

if __name__ == "__main__":
    main()
