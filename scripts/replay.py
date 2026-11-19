"""Deliver the snapshots of a dataset one by one, in the order of manifest.csv.

    uv run python -m scripts.replay data/small-dirty --call "CALL apply_scd2()"

After every snapshot is loaded into stg_orders, the SQL given in --call runs
(your SCD2 procedure). Without --call only the loading is repeated.
"""

import argparse
import csv
import time
from pathlib import Path

from scripts.db import connect
from scripts.load import load_snapshot


def replay(data_dir: Path, call_sql: str | None, limit: int | None) -> None:
    with (data_dir / "manifest.csv").open(newline="", encoding="utf-8") as f:
        manifest = list(csv.DictReader(f))
    if limit is not None:
        manifest = manifest[:limit]

    started = time.perf_counter()
    with connect() as conn:
        for item in manifest:
            step = time.perf_counter()
            rows = load_snapshot(conn, data_dir / item["file"])
            if call_sql:
                conn.execute(call_sql)
                conn.commit()
            print(
                f"{item['file']}: {rows} rows, content {item['content_snapshot']}, "
                f"{time.perf_counter() - step:.2f} s  {item['note']}"
            )
    print(f"Total: {time.perf_counter() - started:.1f} s")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("data_dir", type=Path)
    parser.add_argument("--call", help="SQL to run after each load, e.g. CALL my_proc()")
    parser.add_argument("--limit", type=int, help="deliver only the first N snapshots")
    args = parser.parse_args(argv)
    replay(args.data_dir, args.call, args.limit)


if __name__ == "__main__":
    main()
