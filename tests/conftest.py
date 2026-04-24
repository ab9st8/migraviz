"""Shared fixtures for migraviz tests."""

from __future__ import annotations

import os
import subprocess
import time
import uuid
from pathlib import Path

import pytest
from sqlalchemy import create_engine, text

FIXTURES_DIR = Path(__file__).parent / "fixtures"

PG_PORT = 15432
PG_USER = "migraviz"
PG_PASS = "migraviz"
PG_DB = "migraviz"
PG_IMAGE = "postgres:16-alpine"
CONTAINER_NAME = "migraviz-test-pg"


@pytest.fixture
def alembic_dir() -> Path:
    """Path to the test fixture alembic directory."""
    return FIXTURES_DIR / "alembic"


@pytest.fixture
def alembic_ini() -> Path:
    """Path to the test fixture alembic.ini."""
    return FIXTURES_DIR / "alembic.ini"


def _pg_is_ready(url: str) -> bool:
    try:
        engine = create_engine(url)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        engine.dispose()
        return True
    except Exception:
        return False


@pytest.fixture(scope="session")
def _pg_url():
    """Session-scoped Postgres via plain docker run with a fixed port."""
    url = (
        f"postgresql+psycopg2://{PG_USER}:{PG_PASS}"
        f"@localhost:{PG_PORT}/{PG_DB}"
    )

    # Kill any leftover container from a previous run
    subprocess.run(
        ["docker", "rm", "-f", CONTAINER_NAME],
        capture_output=True,
    )

    subprocess.run(
        [
            "docker", "run", "-d",
            "--name", CONTAINER_NAME,
            "-p", f"{PG_PORT}:5432",
            "-e", f"POSTGRES_USER={PG_USER}",
            "-e", f"POSTGRES_PASSWORD={PG_PASS}",
            "-e", f"POSTGRES_DB={PG_DB}",
            PG_IMAGE,
        ],
        check=True,
        capture_output=True,
    )

    # Wait for postgres to be ready
    for _ in range(30):
        if _pg_is_ready(url):
            break
        time.sleep(1)
    else:
        raise RuntimeError("Postgres container didn't become ready in 30s")

    yield url

    subprocess.run(
        ["docker", "rm", "-f", CONTAINER_NAME],
        capture_output=True,
    )


@pytest.fixture
def pg_url(_pg_url: str):
    """Function-scoped clean database within the shared container."""
    db_name = f"test_{uuid.uuid4().hex[:8]}"

    engine = create_engine(_pg_url, isolation_level="AUTOCOMMIT")
    with engine.connect() as conn:
        conn.execute(text(f"CREATE DATABASE {db_name}"))
    engine.dispose()

    test_url = _pg_url.rsplit("/", 1)[0] + f"/{db_name}"
    yield test_url
