"""Shared fixtures for migraviz tests."""

from pathlib import Path

import pytest
from sqlalchemy import create_engine, text
from testcontainers.postgres import PostgresContainer

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def alembic_dir() -> Path:
    """Path to the test fixture alembic directory."""
    return FIXTURES_DIR / "alembic"


@pytest.fixture
def alembic_ini() -> Path:
    """Path to the test fixture alembic.ini."""
    return FIXTURES_DIR / "alembic.ini"


@pytest.fixture(scope="session")
def _pg_container():
    """Session-scoped Postgres container. Shared across all tests."""
    with PostgresContainer("postgres:16-alpine") as pg:
        yield pg


@pytest.fixture
def pg_url(_pg_container):
    """Function-scoped clean database URL.

    Creates a fresh database for each test within the shared container,
    so tests don't interfere with each other.
    """
    import uuid

    db_name = f"test_{uuid.uuid4().hex[:8]}"
    admin_url = _pg_container.get_connection_url()

    engine = create_engine(admin_url, isolation_level="AUTOCOMMIT")
    with engine.connect() as conn:
        conn.execute(text(f"CREATE DATABASE {db_name}"))
    engine.dispose()

    # Build URL for the new database
    test_url = admin_url.rsplit("/", 1)[0] + f"/{db_name}"
    yield test_url
