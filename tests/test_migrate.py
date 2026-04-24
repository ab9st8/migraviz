"""Tests for migration replay against an ephemeral DB."""

from pathlib import Path

import pytest
from sqlalchemy import create_engine, text


@pytest.mark.integration
def test_migrate_to_head_creates_tables(alembic_ini: Path, pg_url: str):
    """Running migrations to head should create all tables."""
    from migraviz.migrate import run_migrations

    run_migrations(alembic_ini, pg_url, revision="head")

    engine = create_engine(pg_url)
    with engine.connect() as conn:
        result = conn.execute(
            text(
                "SELECT table_name FROM information_schema.tables "
                "WHERE table_schema = 'public' "
                "ORDER BY table_name"
            )
        )
        tables = [row[0] for row in result]
    engine.dispose()

    assert "users" in tables
    assert "posts" in tables


@pytest.mark.integration
def test_migrate_to_specific_revision(alembic_ini: Path, pg_url: str):
    """Migrating to the first revision should only create users."""
    from migraviz.migrate import run_migrations

    run_migrations(alembic_ini, pg_url, revision="aaa001")

    engine = create_engine(pg_url)
    with engine.connect() as conn:
        result = conn.execute(
            text(
                "SELECT table_name FROM information_schema.tables "
                "WHERE table_schema = 'public' "
                "ORDER BY table_name"
            )
        )
        tables = [row[0] for row in result]
    engine.dispose()

    assert "users" in tables
    assert "posts" not in tables
