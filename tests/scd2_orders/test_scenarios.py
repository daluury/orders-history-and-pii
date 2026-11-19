"""Basic scenarios for the SCD2 solution.

Each scenario is a stub: write the data setup, the call and the check.
The data comes from the generator (``uv run python -m generator --size small --mode dirty``)
or from a few rows inserted by hand.
"""

import pytest

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skip(reason="TODO: the solution is not written yet"),
]


def test_first_load():
    """Empty history + first snapshot: one current version per order."""


def test_status_change_creates_new_version():
    """Next snapshot with a changed status closes the old version and opens a new one."""


def test_same_snapshot_twice_changes_nothing():
    """Idempotence: loading the same snapshot again leaves orders_history as it was."""


def test_late_snapshot_does_not_break_history():
    """An older snapshot after a newer one: no overwrite, missing versions inserted."""


def test_order_missing_from_snapshot():
    """The rule written in docs/decisions.md: the version stays open or is closed."""
