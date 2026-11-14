"""Run every query in a .sql file, print the results and save each one as a CSV in outputs/.

Usage (from the project root):
    python src/run_sql.py sql/01_data_quality.sql
    python src/run_sql.py sql/02_business_questions.sql

Each query must end with a semicolon and start with a comment line such as "-- Q1. Overall KPIs".
Avoid semicolons inside comments.
"""
import re
import sqlite3
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "olist.db"
OUT_DIR = ROOT / "outputs"


def split_queries(text: str):
    queries = []
    for chunk in text.split(";"):
        lines = chunk.strip().splitlines()
        first_code = next(
            (i for i, ln in enumerate(lines) if ln.strip() and not ln.strip().startswith("--")),
            None,
        )
        if first_code is None:
            continue
        # The title is the comment line right above the first line of SQL.
        comments = [ln.lstrip("- ").strip() for ln in lines[:first_code] if ln.strip()]
        title = comments[-1] if comments else "query"
        queries.append((title, chunk.strip()))
    return queries


def slugify(title: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", title.lower()).strip("_")[:60]


def main() -> None:
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(1)
    if not DB_PATH.exists():
        print("olist.db not found. Run  python src/load_data.py  first.")
        sys.exit(1)

    sql_path = Path(sys.argv[1])
    OUT_DIR.mkdir(exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    try:
        for title, sql in split_queries(sql_path.read_text(encoding="utf-8")):
            df = pd.read_sql_query(sql, conn)
            print(f"\n=== {title} ===")
            print(df.to_string(index=False) if not df.empty else "(no rows)")
            df.to_csv(OUT_DIR / f"{slugify(title)}.csv", index=False)
    finally:
        conn.close()
    print(f"\nResults saved to {OUT_DIR.name}/")


if __name__ == "__main__":
    main()
