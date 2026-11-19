"""Load CSV files into PostgreSQL.

    uv run python -m scripts.load init
    uv run python -m scripts.load snapshot data/small-dirty/snapshot_01.csv
    uv run python -m scripts.load users-protected path/to/users_protected.csv

``snapshot`` replaces the content of stg_orders (it is a current-state snapshot).
``users-protected`` replaces the content of users_protected; the columns are
taken from the CSV header, so their order does not matter.
"""

import argparse
import csv
from pathlib import Path

import psycopg

from scripts.db import ROOT, connect

CHUNK = 1 << 20  # copy the file in 1 MiB pieces, not all at once


def _copy_csv(cur: psycopg.Cursor, table: str, path: Path) -> int:
    with path.open(newline="", encoding="utf-8") as f:
        columns = next(csv.reader(f))
    column_list = ", ".join(columns)
    statement = f"COPY {table} ({column_list}) FROM STDIN WITH (FORMAT csv, HEADER true)"
    with path.open("rb") as f, cur.copy(statement) as copy:
        while chunk := f.read(CHUNK):
            copy.write(chunk)
    return cur.rowcount


def init_schema(conn: psycopg.Connection) -> None:
    """Apply sql/schema.sql (safe to repeat: CREATE TABLE IF NOT EXISTS)."""
    conn.execute((ROOT / "sql" / "schema.sql").read_text(encoding="utf-8"))
    conn.commit()


def load_snapshot(conn: psycopg.Connection, path: Path) -> int:
    """Replace stg_orders with the snapshot file; return the number of rows."""
    with conn.cursor() as cur:
        cur.execute("TRUNCATE stg_orders")
        rows = _copy_csv(cur, "stg_orders", path)
    conn.commit()
    return rows


def load_users_protected(conn: psycopg.Connection, path: Path) -> int:
    """Replace users_protected with the protected CSV; return the number of rows."""
    with conn.cursor() as cur:
        cur.execute("TRUNCATE users_protected")
        rows = _copy_csv(cur, "users_protected", path)
    conn.commit()
    return rows


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("init", help="apply sql/schema.sql")
    for name in ("snapshot", "users-protected"):
        sub.add_parser(name).add_argument("file", type=Path)
    args = parser.parse_args(argv)

    with connect() as conn:
        if args.command == "init":
            init_schema(conn)
            print("Schema applied")
        elif args.command == "snapshot":
            print(f"stg_orders: {load_snapshot(conn, args.file)} rows from {args.file}")
        else:
            print(f"users_protected: {load_users_protected(conn, args.file)} rows")


if __name__ == "__main__":
    main()
