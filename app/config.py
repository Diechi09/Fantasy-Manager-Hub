import os
from pathlib import Path

DB_PATH = os.getenv(
    "DB_PATH",
    str(Path(__file__).resolve().parents[1] / "fantasy.db")
)

def get_db_path() -> str:
    return DB_PATH
