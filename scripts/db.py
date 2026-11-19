"""Connection to the project PostgreSQL (settings come from .env)."""

import os
from pathlib import Path

import psycopg
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent


def connect(dbname: str | None = None) -> psycopg.Connection:
    """Open a connection; the short timeout fails fast if the container is down."""
    load_dotenv(ROOT / ".env")
    return psycopg.connect(
        host=os.environ.get("POSTGRES_HOST", "127.0.0.1"),
        port=int(os.environ.get("POSTGRES_PORT", "5434")),
        user=os.environ["POSTGRES_USER"],
        password=os.environ["POSTGRES_PASSWORD"],
        dbname=dbname or os.environ["POSTGRES_DB"],
        connect_timeout=3,
    )
