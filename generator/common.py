"""Shared helpers: one seeded Faker per run."""

from faker import Faker


def make_faker(seed: int | None = None) -> Faker:
    """Create the only Faker of a run, optionally seeded.

    All random choices in the generator must come from this object
    (``fake.random`` for the standard ``random`` API), so the same seed
    gives the same data.
    """
    fake = Faker()
    if seed is not None:
        fake.seed_instance(seed)
    return fake


def weighted_choice(fake: Faker, options: tuple[tuple[str, float], ...]) -> str:
    """Pick one value from (value, weight) pairs using the seeded generator."""
    values = [value for value, _ in options]
    weights = [weight for _, weight in options]
    return fake.random.choices(values, weights=weights, k=1)[0]
