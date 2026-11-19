"""Email protection: HMAC pseudonym + reversible encryption.

Only the contract is fixed here (docs/problem-statement.md, Part B), the bodies are still
to be written. Signatures can be changed if the design needs it, but then update the
docstring and docs/pii-protection.md.
"""

from pathlib import Path


def canonicalize_email(email: str) -> str:
    """Canonical form before any processing (spaces, case)."""
    raise NotImplementedError


def load_keys_from_env() -> tuple[bytes, bytes]:
    """Read the HMAC key and the encryption key from PII_HMAC_KEY / PII_ENCRYPTION_KEY."""
    raise NotImplementedError


def protect_csv(
    input_path: Path,
    output_path: Path,
    quarantine_path: Path,
    hmac_key: bytes,
    encryption_key: bytes,
) -> dict[str, int]:
    """Read users CSV in chunks, write the protected CSV and a quarantine file.

    - `email` is replaced by `email_pseudonym` (HMAC: the same email gives the same value)
      and `email_encrypted` (can be reversed with the key);
    - rows with an invalid email go to the quarantine file with the reason, the run goes on;
    - other fields pass unchanged (names and phone: see docs/decisions.md);
    - memory does not grow with the file size.

    Returns counters, for example rows read, protected and quarantined.
    """
    raise NotImplementedError


def decrypt_email(email_encrypted: str, encryption_key: bytes) -> str:
    """Return the original (canonical) email from `email_encrypted`."""
    raise NotImplementedError
