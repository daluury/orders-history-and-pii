"""Command line entry point: uv run python -m generator --size small --mode dirty."""

import argparse
import json
import time
from pathlib import Path

from generator import config
from generator.common import make_faker
from generator.orders import write_orders
from generator.users import write_users


def generate(size_name: str, mode: str, seed: int, out_dir: Path) -> dict[str, int]:
    """Generate one dataset into out_dir and return the counters."""
    size = config.SIZES[size_name]
    out_dir.mkdir(parents=True, exist_ok=True)
    fake = make_faker(seed)  # one Faker per run, users first, then orders

    counters = write_users(fake, size.users, mode, out_dir)
    counters.update(write_orders(fake, size.users, size, mode, out_dir))

    params = {"size": size_name, "mode": mode, "seed": seed, **counters}
    (out_dir / "params.json").write_text(json.dumps(params, indent=2) + "\n", encoding="utf-8")
    return params


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Generate users and order snapshots.")
    parser.add_argument("--size", choices=config.SIZES, default="small")
    parser.add_argument("--mode", choices=config.MODES, default="clean")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="output folder (default: data/<size>-<mode>)",
    )
    args = parser.parse_args(argv)

    out_dir = args.out or Path("data") / f"{args.size}-{args.mode}"
    started = time.perf_counter()
    params = generate(args.size, args.mode, args.seed, out_dir)
    elapsed = time.perf_counter() - started

    print(f"Written to {out_dir} in {elapsed:.1f} s")
    for key, value in params.items():
        print(f"  {key}: {value}")


if __name__ == "__main__":
    main()
