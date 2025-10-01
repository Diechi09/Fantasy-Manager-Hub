import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

def run(script: str, *args: str):
    cmd = [sys.executable, str(ROOT / "app" / "ingest" / script), *args]
    print(">", " ".join(cmd))
    res = subprocess.run(cmd)
    if res.returncode != 0:
        sys.exit(res.returncode)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", required=True)
    args = ap.parse_args()
    run("sleeper_ingest.py")
    run("valuations_ingest.py", args.csv)
    run("trending_ingest.py")

if __name__ == "__main__":
    main()
