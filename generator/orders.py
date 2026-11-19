"""Order snapshots generator and the expected SCD2 history.

The source keeps one row per order with the current status. Every hour a
snapshot of all orders is delivered (``snapshot_NN.csv``, NN is the delivery
number). The generator simulates the orders hour by hour and, because it knows
what really happened, writes the expected result (``expected_history.csv``).

Rules that keep the expected history unambiguous:

- an order changes status at most once per hour, so every status is visible
  in at least one snapshot (the first hidden state of the initial orders is
  not part of the history: it was never delivered);
- the expected history contains every version that is visible in at least one
  delivered snapshot, including versions that arrive only in a late snapshot.

Dirty mode adds four traps (see traps.csv):

1. one snapshot is delivered twice in a row;
2. one snapshot arrives after the next one (late, older content);
3. duplicated rows inside a snapshot;
4. an order is missing from one snapshot and comes back in the next one.
"""

import csv
import datetime
import shutil
from pathlib import Path

from faker import Faker

from generator import config
from generator.common import weighted_choice

SNAPSHOT_FIELDS = ("order_id", "customer_id", "status", "updated_at")
HISTORY_FIELDS = (
    "order_id",
    "customer_id",
    "status",
    "valid_from",
    "valid_to",
    "is_current",
)
FMT = "%Y-%m-%d %H:%M:%S"


def _plan_deliveries(fake: Faker, n_snapshots: int, dirty: bool):
    """Delivery order of snapshot contents and the trap descriptions.

    Returns (deliveries, late_content): deliveries is a list of content numbers
    (1-based) in the order of arrival, late_content is the content that arrives
    after the next one (None in clean mode).
    """
    deliveries = list(range(1, n_snapshots + 1))
    if not dirty or n_snapshots < 3:
        return deliveries, None

    late = fake.random.randint(1, n_snapshots - 1)  # content `late` arrives after `late + 1`
    deliveries[late - 1], deliveries[late] = deliveries[late], deliveries[late - 1]

    repeat = fake.random.randint(1, n_snapshots)
    position = deliveries.index(repeat)
    deliveries.insert(position + 1, repeat)
    return deliveries, late


def _at(offset_seconds: int) -> str:
    """Timestamp string `offset_seconds` after the generator start."""
    return (config.START + datetime.timedelta(seconds=offset_seconds)).strftime(FMT)


def write_orders(
    fake: Faker, n_users: int, size: config.Size, mode: str, out_dir: Path
) -> dict[str, int]:
    """Write snapshots, manifest, traps and the expected history."""
    dirty = mode == "dirty"
    n_snapshots = size.snapshots
    interval_seconds = int(config.SNAPSHOT_INTERVAL.total_seconds())
    deliveries, late = _plan_deliveries(fake, n_snapshots, dirty)

    vanish_snapshots: set[int] = set()
    if dirty and n_snapshots >= 3:
        wanted = min(size.vanished, n_snapshots - 2)
        vanish_snapshots = set(fake.random.sample(range(2, n_snapshots), k=wanted))
    # how many orders to hide in each of those snapshots
    per_snapshot_vanish = (
        max(1, size.vanished // max(1, len(vanish_snapshots))) if vanish_snapshots else 0
    )

    # --- order state, index = order_id - 1 -----------------------------------
    customer: list[int] = []
    status: list[str] = []
    updated: list[str] = []
    created_in: list[int] = []  # interval of creation (0 = before the first snapshot)
    changed_in: list[int] = []  # interval of the last status change
    versions: list[list[tuple[str, str]]] = []  # (updated_at, status) per order
    observed: list[int] = []  # bit mask: version i seen in a delivered snapshot

    def add_order(interval: int, status_name: str, ts: str) -> None:
        customer.append(fake.random.randint(1, n_users))
        status.append(status_name)
        updated.append(ts)
        created_in.append(interval)
        changed_in.append(interval)
        versions.append([(ts, status_name)])
        observed.append(0)

    for _ in range(size.initial_orders):
        # initial orders were last updated during the 24 hours before the start
        ts = _at(-fake.random.randint(0, 24 * 3600 - 1))
        add_order(0, weighted_choice(fake, config.INITIAL_STATUS_WEIGHTS), ts)

    # --- file names by delivery -------------------------------------------------
    first_file: dict[int, str] = {}
    copies: list[tuple[int, str]] = []  # (content, file) of repeated deliveries
    manifest: list[tuple[int, str, int, str, str]] = []
    traps: list[tuple[str, str, str]] = []
    seen_content: set[int] = set()
    for number, content in enumerate(deliveries, start=1):
        file_name = f"snapshot_{number:02d}.csv"
        snapshot_time = _at(content * interval_seconds)
        note = ""
        if content in seen_content:
            copies.append((content, file_name))
            note = f"repeat of snapshot content {content}"
            traps.append(("repeat_snapshot", file_name, ""))
        else:
            first_file[content] = file_name
            seen_content.add(content)
            if content == late:
                note = "late: arrives after newer content"
                traps.append(("late_snapshot", file_name, ""))
        manifest.append((number, file_name, content, snapshot_time, note))

    vanished_prev: set[int] = set()
    duplicate_rows = 0
    vanished_total = 0

    for k in range(1, n_snapshots + 1):
        interval_start = (k - 1) * interval_seconds
        existing = len(customer)

        # status changes: at most one per order and hour
        for i in range(existing):
            current = status[i]
            options = config.TRANSITIONS.get(current)
            if options is None or fake.random.random() >= config.P_ADVANCE:
                continue
            new_status = weighted_choice(fake, options)
            ts = _at(interval_start + fake.random.randint(1, interval_seconds))
            status[i] = new_status
            updated[i] = ts
            changed_in[i] = k
            versions[i].append((ts, new_status))

        # new orders
        for _ in range(fake.random.randint(size.new_orders_min, size.new_orders_max)):
            ts = _at(interval_start + fake.random.randint(1, interval_seconds))
            add_order(k, "new", ts)

        # orders hidden in this snapshot: present before, unchanged this hour
        hidden: set[int] = set()
        if k in vanish_snapshots:
            candidates = [
                i for i in range(existing) if changed_in[i] < k and i not in vanished_prev
            ]
            take = min(per_snapshot_vanish, len(candidates))
            hidden = set(fake.random.sample(candidates, k=take))
        vanished_prev = hidden
        vanished_total += len(hidden)

        rows = []
        for i in range(len(customer)):
            if i in hidden:
                continue
            rows.append((i + 1, customer[i], status[i], updated[i]))
            observed[i] |= 1 << (len(versions[i]) - 1)

        extra: list[tuple[int, int, str, str]] = []
        if dirty:
            n_dup = max(1, round(len(rows) * config.DIRTY_DUPLICATE_ROWS_RATE))
            extra = [rows[j] for j in fake.random.sample(range(len(rows)), k=n_dup)]
            rows = rows + extra
            fake.random.shuffle(rows)
            duplicate_rows += len(extra)

        file_name = first_file[k]
        with (out_dir / file_name).open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f, lineterminator="\n")
            writer.writerow(SNAPSHOT_FIELDS)
            writer.writerows(rows)
        for row in extra:
            traps.append(("duplicate_row", file_name, str(row[0])))
        for i in sorted(hidden):
            traps.append(("vanished_order", file_name, str(i + 1)))

    for content, file_name in copies:
        shutil.copyfile(out_dir / first_file[content], out_dir / file_name)

    with (out_dir / "manifest.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, lineterminator="\n")
        writer.writerow(("delivery", "file", "content_snapshot", "snapshot_time", "note"))
        writer.writerows(manifest)

    if dirty:
        with (out_dir / "traps.csv").open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f, lineterminator="\n")
            writer.writerow(("trap", "file", "order_id"))
            writer.writerows(traps)

    history_rows = _write_expected_history(out_dir, customer, versions, observed)

    return {
        "orders": len(customer),
        "snapshot_files": len(deliveries),
        "history_rows": history_rows,
        "duplicate_rows": duplicate_rows,
        "vanished_orders": vanished_total,
    }


def _write_expected_history(out_dir, customer, versions, observed) -> int:
    """expected_history.csv: every delivered version with valid_from/valid_to."""
    count = 0
    with (out_dir / "expected_history.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, lineterminator="\n")
        writer.writerow(HISTORY_FIELDS)
        for i, order_versions in enumerate(versions):
            seen = [v for idx, v in enumerate(order_versions) if observed[i] >> idx & 1]
            for pos, (ts, status_name) in enumerate(seen):
                is_last = pos == len(seen) - 1
                valid_to = "" if is_last else seen[pos + 1][0]
                writer.writerow(
                    (
                        i + 1,
                        customer[i],
                        status_name,
                        ts,
                        valid_to,
                        "true" if is_last else "false",
                    )
                )
                count += 1
    return count
