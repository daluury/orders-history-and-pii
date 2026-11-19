"""Basic checks for the email protection.

Each check is a stub: write the setup and the assertion. Test data: users.csv from
``uv run python -m generator --size small --mode dirty`` (non-canonical, invalid and
duplicated emails are there; the expected quarantine is in expected_users_quarantine.csv).
"""

import pytest

pytestmark = pytest.mark.skip(reason="TODO: the function is not written yet")


def test_canonicalization():
    """Spaces and case do not change the result."""


def test_pseudonym_is_repeatable():
    """The same email (any case or spaces) gives the same email_pseudonym."""


def test_decrypt_returns_original_email():
    """decrypt_email(email_encrypted, key) gives back the canonical email."""


def test_invalid_email_goes_to_quarantine():
    """Invalid rows land in the quarantine file with a reason and do not stop the run."""


def test_memory_stays_flat_on_big_file():
    """Measure peak memory on the large users.csv (1 million rows) and write it down."""
