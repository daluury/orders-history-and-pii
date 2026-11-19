"""Compare the orders_history table with expected_history.csv of a dataset.

    uv run python -m scripts.diff_history data/small-dirty

Rows are matched by (order_id, valid_from). A NULL valid_to is compared as an
empty value; if the solution uses another placeholder, the difference is shown.
"""

import argparse
import csv
from pathlib import Path

from scripts.db import connect

COLUMNS = ("order_id", "customer_id", "status", "valid_from", "valid_to", "is_current")
QUERY = """
    SELECT order_id, customer_id, status,
           to_char(valid_from, 'YYYY-MM-DD HH24:MI:SS'),
           coalesce(to_char(valid_to, 'YYYY-MM-DD HH24:MI:SS'), ''),
           CASE WHEN is_current THEN 'true' ELSE 'false' END
    FROM orders_history
"""


def diff(data_dir: Path, show: int = 10) -> int:
    """Print the differences and return their number."""
    with (data_dir / "expected_history.csv").open(newline="", encoding="utf-8") as f:
        expected = {
            (r["order_id"], r["valid_from"]): tuple(r[c] for c in COLUMNS)
            for r in csv.DictReader(f)
        }
    with connect() as conn:
        actual = {(str(row[0]), row[3]): tuple(str(v) for v in row) for row in conn.execute(QUERY)}

    missing = sorted(expected.keys() - actual.keys())
    extra = sorted(actual.keys() - expected.keys())
    different = sorted(k for k in expected.keys() & actual.keys() if expected[k] != actual[k])

    print(f"expected {len(expected)} rows, orders_history has {len(actual)} rows")
    for title, keys, source in (
        ("missing in orders_history", missing, expected),
        ("not expected", extra, actual),
    ):
        print(f"{title}: {len(keys)}")
        for key in keys[:show]:
            print("   ", source[key])
    print(f"different values: {len(different)}")
    for key in different[:show]:
        print("    expected:", expected[key])
        print("    actual:  ", actual[key])
    return len(missing) + len(extra) + len(different)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("data_dir", type=Path)
    args = parser.parse_args(argv)
    raise SystemExit(1 if diff(args.data_dir) else 0)


if __name__ == "__main__":
    main()
