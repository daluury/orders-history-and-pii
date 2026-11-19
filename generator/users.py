"""users.csv generator: customers with personal data.

In dirty mode a few emails are made non-canonical (spaces, upper case),
invalid (must go to quarantine) or duplicated (same email, other case).
The invalid ones are listed in expected_users_quarantine.csv.
"""

import csv
import datetime
from pathlib import Path

from faker import Faker

from generator import config
from generator.common import weighted_choice

USER_FIELDS = (
    "customer_id",
    "email",
    "first_name",
    "last_name",
    "phone",
    "country",
    "registration_date",
    "subscription_type",
)

# (how the broken email is built from a normal one, reason for the quarantine)
INVALID_KINDS = ("empty", "no_at_sign", "no_domain", "multiple_at", "whitespace_inside")


def _base_email(fake: Faker, customer_id: int, first: str, last: str) -> str:
    domain = fake.random_element(config.EMAIL_DOMAINS)
    # the customer_id in the local part keeps emails unique in a big file
    return f"{first}.{last}{customer_id}@{domain}".lower()


def _break_email(email: str, kind: str) -> str:
    local, domain = email.split("@")
    return {
        "empty": "",
        "no_at_sign": f"{local}{domain}",
        "no_domain": f"{local}@",
        "multiple_at": f"{local}@@{domain}",
        "whitespace_inside": f"{local[:3]} {local[3:]}@{domain}",
    }[kind]


def _messy_case(fake: Faker, email: str) -> str:
    """Non-canonical but valid: spaces around and a different case."""
    variants = (email.upper(), email.capitalize(), email.title())
    return f" {fake.random_element(variants)} "


def _pick_special_ids(fake: Faker, n_users: int) -> dict[int, str]:
    """Customer ids of dirty rows with their kind (at least one of each)."""
    rates = (
        ("non_canonical", config.DIRTY_NON_CANONICAL_RATE),
        ("invalid", config.DIRTY_INVALID_RATE),
        ("duplicate", config.DIRTY_DUPLICATE_EMAIL_RATE),
    )
    counts = [(kind, max(1, round(n_users * rate))) for kind, rate in rates]
    chosen = fake.random.sample(range(1, n_users + 1), k=sum(c for _, c in counts))
    special: dict[int, str] = {}
    position = 0
    for kind, count in counts:
        for customer_id in chosen[position : position + count]:
            special[customer_id] = kind
        position += count
    return special


def write_users(fake: Faker, n_users: int, mode: str, out_dir: Path) -> dict[str, int]:
    """Write users.csv (and the quarantine oracle); return counters."""
    dirty = mode == "dirty"

    # first pass: names and normal emails (the duplicates need a partner email)
    names = [(fake.first_name(), fake.last_name()) for _ in range(n_users)]
    emails = [_base_email(fake, i + 1, first, last) for i, (first, last) in enumerate(names)]
    special = _pick_special_ids(fake, n_users) if dirty else {}
    normal_ids = [i for i in range(1, n_users + 1) if i not in special]

    quarantine: list[tuple[int, str, str]] = []
    counters = {"non_canonical": 0, "invalid": 0, "duplicate": 0}
    days = (config.REGISTRATION_TO - config.REGISTRATION_FROM).days

    with (out_dir / "users.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, lineterminator="\n")
        writer.writerow(USER_FIELDS)
        for customer_id in range(1, n_users + 1):
            first, last = names[customer_id - 1]
            email = emails[customer_id - 1]
            kind = special.get(customer_id)
            if kind == "non_canonical":
                email = _messy_case(fake, email)
            elif kind == "invalid":
                reason = fake.random_element(INVALID_KINDS)
                email = _break_email(email, reason)
                quarantine.append((customer_id, reason, email))
            elif kind == "duplicate":
                partner = fake.random_element(normal_ids)
                email = _messy_case(fake, emails[partner - 1])
            if kind:
                counters[kind] += 1

            registration = config.REGISTRATION_FROM + datetime.timedelta(
                days=fake.random.randint(0, days)
            )
            writer.writerow(
                (
                    customer_id,
                    email,
                    first,
                    last,
                    fake.phone_number(),
                    fake.random_element(config.COUNTRIES),
                    registration.isoformat(),
                    weighted_choice(fake, config.SUBSCRIPTIONS),
                )
            )

    with (out_dir / "expected_users_quarantine.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, lineterminator="\n")
        writer.writerow(("customer_id", "reason", "raw_email"))
        writer.writerows(quarantine)

    counters["users"] = n_users
    return counters
