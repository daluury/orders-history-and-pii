"""Dataset sizes, statuses and the fixed time frame of the generator."""

import datetime
from dataclasses import dataclass

# fixed start, not "today", so the same seed gives the same data on any day
START = datetime.datetime(2026, 1, 1, 0, 0, 0)
SNAPSHOT_INTERVAL = datetime.timedelta(hours=1)
REGISTRATION_FROM = datetime.date(2018, 1, 1)
REGISTRATION_TO = datetime.date(2025, 12, 31)

STATUSES = ("new", "processing", "shipped", "delivered", "cancelled")

# allowed transitions with probabilities; delivered and cancelled are final
TRANSITIONS: dict[str, tuple[tuple[str, float], ...]] = {
    "new": (("processing", 0.85), ("cancelled", 0.15)),
    "processing": (("shipped", 0.85), ("cancelled", 0.15)),
    "shipped": (("delivered", 1.0),),
}

# chance that a non-final order moves to the next status in one hour
P_ADVANCE = 0.35

# statuses (with weights) of the orders that exist before the first snapshot
INITIAL_STATUS_WEIGHTS = (
    ("new", 0.2),
    ("processing", 0.3),
    ("shipped", 0.2),
    ("delivered", 0.2),
    ("cancelled", 0.1),
)

COUNTRIES = (
    "US",
    "GB",
    "DE",
    "FR",
    "ES",
    "IT",
    "PL",
    "NL",
    "SE",
    "CA",
    "AU",
    "BR",
)
EMAIL_DOMAINS = (
    "gmail.com",
    "yahoo.com",
    "outlook.com",
    "icloud.com",
    "proton.me",
    "example.org",
    "mail.com",
    "fastmail.com",
)
SUBSCRIPTIONS = (("free", 0.6), ("basic", 0.3), ("premium", 0.1))

# share of users with a non-canonical, invalid or duplicated email (dirty mode)
DIRTY_NON_CANONICAL_RATE = 0.03
DIRTY_INVALID_RATE = 0.01
DIRTY_DUPLICATE_EMAIL_RATE = 0.01
# share of duplicated rows inside one snapshot (dirty mode)
DIRTY_DUPLICATE_ROWS_RATE = 0.02


@dataclass(frozen=True)
class Size:
    users: int
    initial_orders: int
    snapshots: int
    new_orders_min: int  # new orders per snapshot interval
    new_orders_max: int
    vanished: int  # orders that disappear from one snapshot (dirty mode)


SIZES: dict[str, Size] = {
    # tens of orders: can be read by eye
    "small": Size(
        users=20, initial_orders=15, snapshots=6, new_orders_min=3, new_orders_max=5, vanished=2
    ),
    # for scenarios
    "medium": Size(
        users=10_000,
        initial_orders=5_000,
        snapshots=24,
        new_orders_min=300,
        new_orders_max=700,
        vanished=20,
    ),
    # load check: 1 million users, hundreds of thousands of orders
    "large": Size(
        users=1_000_000,
        initial_orders=200_000,
        snapshots=12,
        new_orders_min=3_000,
        new_orders_max=7_000,
        vanished=300,
    ),
}

MODES = ("clean", "dirty")
