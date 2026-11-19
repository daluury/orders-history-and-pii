"""Tests of the data generator (small size, no database)."""

import csv
import itertools
from pathlib import Path

import pytest

from generator import config
from generator.cli import generate


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


@pytest.fixture(scope="module")
def clean(tmp_path_factory) -> Path:
    out = tmp_path_factory.mktemp("clean")
    generate("small", "clean", 42, out)
    return out


@pytest.fixture(scope="module")
def dirty(tmp_path_factory) -> Path:
    out = tmp_path_factory.mktemp("dirty")
    generate("small", "dirty", 42, out)
    return out


def test_same_seed_gives_same_files(tmp_path, dirty):
    again = tmp_path / "again"
    generate("small", "dirty", 42, again)
    for path in dirty.iterdir():
        assert path.read_bytes() == (again / path.name).read_bytes(), path.name


def test_other_seed_gives_other_data(tmp_path, dirty):
    other = tmp_path / "other"
    generate("small", "dirty", 7, other)
    assert (dirty / "users.csv").read_bytes() != (other / "users.csv").read_bytes()


def test_clean_mode_has_no_traps(clean):
    assert not (clean / "traps.csv").exists()
    manifest = read_csv(clean / "manifest.csv")
    assert [int(m["content_snapshot"]) for m in manifest] == list(range(1, 7))
    for m in manifest:
        rows = read_csv(clean / m["file"])
        ids = [r["order_id"] for r in rows]
        assert len(ids) == len(set(ids))
    assert read_csv(clean / "expected_users_quarantine.csv") == []


def test_users_clean_are_canonical_and_unique(clean):
    emails = [u["email"] for u in read_csv(clean / "users.csv")]
    assert all(e == e.strip().lower() and e.count("@") == 1 for e in emails)
    assert len(emails) == len(set(emails))


def reference_history(out: Path) -> dict[str, list[tuple[str, str, str]]]:
    """Naive rebuild: every distinct (status, updated_at) seen in any file."""
    versions: dict[str, set[tuple[str, str, str]]] = {}
    for m in read_csv(out / "manifest.csv"):
        for r in read_csv(out / m["file"]):
            versions.setdefault(r["order_id"], set()).add(
                (r["updated_at"], r["status"], r["customer_id"])
            )
    return {oid: sorted(v) for oid, v in versions.items()}


@pytest.mark.parametrize("fixture_name", ["clean", "dirty"])
def test_expected_history_matches_delivered_versions(fixture_name, request):
    out = request.getfixturevalue(fixture_name)
    reference = reference_history(out)
    expected: dict[str, list[dict[str, str]]] = {}
    for row in read_csv(out / "expected_history.csv"):
        expected.setdefault(row["order_id"], []).append(row)

    assert set(expected) == set(reference)
    for oid, rows in expected.items():
        assert [(r["valid_from"], r["status"], r["customer_id"]) for r in rows] == reference[oid]
        # chain of versions: valid_to is the next valid_from, only the last is current
        for current, following in itertools.pairwise(rows):
            assert current["valid_to"] == following["valid_from"]
            assert current["is_current"] == "false"
        assert rows[-1]["valid_to"] == "" and rows[-1]["is_current"] == "true"


@pytest.mark.parametrize("fixture_name", ["clean", "dirty"])
def test_status_changes_follow_allowed_transitions(fixture_name, request):
    out = request.getfixturevalue(fixture_name)
    by_order: dict[str, list[str]] = {}
    for row in read_csv(out / "expected_history.csv"):
        by_order.setdefault(row["order_id"], []).append(row["status"])
    for statuses in by_order.values():
        for before, after in itertools.pairwise(statuses):
            allowed = {s for s, _ in config.TRANSITIONS.get(before, ())}
            assert after in allowed, (before, after)


def test_dirty_repeat_and_late_snapshots(dirty):
    manifest = read_csv(dirty / "manifest.csv")
    contents = [int(m["content_snapshot"]) for m in manifest]
    repeat = [m for m in manifest if m["note"].startswith("repeat")]
    late = [m for m in manifest if m["note"].startswith("late")]
    assert len(repeat) == 1 and len(late) == 1

    repeat_content = int(repeat[0]["content_snapshot"])
    first = next(m for m in manifest if int(m["content_snapshot"]) == repeat_content)
    assert (dirty / repeat[0]["file"]).read_bytes() == (dirty / first["file"]).read_bytes()

    late_content = int(late[0]["content_snapshot"])
    assert contents.index(late_content) > contents.index(late_content + 1)


def test_dirty_duplicates_and_vanished_orders(dirty):
    traps = read_csv(dirty / "traps.csv")
    duplicates = [t for t in traps if t["trap"] == "duplicate_row"]
    assert duplicates
    for trap in duplicates:
        ids = [r["order_id"] for r in read_csv(dirty / trap["file"])]
        assert ids.count(trap["order_id"]) >= 2

    manifest = read_csv(dirty / "manifest.csv")
    by_content = {int(m["content_snapshot"]): m["file"] for m in manifest}
    vanished = [t for t in traps if t["trap"] == "vanished_order"]
    assert vanished
    for trap in vanished:
        content = next(c for c, f in by_content.items() if f == trap["file"])
        before = {r["order_id"] for r in read_csv(dirty / by_content[content - 1])}
        after = {r["order_id"] for r in read_csv(dirty / by_content[content + 1])}
        here = {r["order_id"] for r in read_csv(dirty / trap["file"])}
        assert trap["order_id"] in before and trap["order_id"] in after
        assert trap["order_id"] not in here


def test_dirty_users_quarantine_oracle(dirty):
    users = {u["customer_id"]: u["email"] for u in read_csv(dirty / "users.csv")}
    quarantine = read_csv(dirty / "expected_users_quarantine.csv")
    assert quarantine
    for q in quarantine:
        assert users[q["customer_id"]] == q["raw_email"]
        email = q["raw_email"].strip()
        assert not email or email.count("@") != 1 or " " in email or email.endswith("@")

    # canonical valid emails: one duplicated pair differs only by case and spaces
    bad = {q["customer_id"] for q in quarantine}
    canonical = [e.strip().lower() for c, e in users.items() if c not in bad]
    assert len(canonical) - len(set(canonical)) >= 1
    assert any(e != e.strip().lower() for c, e in users.items() if c not in bad)
