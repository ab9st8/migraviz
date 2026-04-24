"""Tests for migration replay against an ephemeral DB."""

from pathlib import Path

import pytest
from sqlalchemy import create_engine, text


@pytest.mark.integration
def test_migrate_to_head_creates_tables(alembic_ini: Path):
    """Running migrations to head should create all tables."""
    from migraviz.db import ephemeral_pg
    from migraviz.migrate import run_migrations

    with ephemeral_pg() as url:
        run_migrations(alembic_ini, url, revision="head")

        engine = create_engine(url)
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

    # alembic_version is alembic's bookkeeping, users and posts are ours
    assert "users" in tables
    assert "posts" in tables


@pytest.mark.integration
def test_migrate_to_specific_revision(alembic_ini: Path):
    """Migrating to the first revision should only create users."""
    from migraviz.db import ephemeral_pg
    from migraviz.migrate import run_migrations

    with ephemeral_pg() as url:
        run_migrations(alembic_ini, url, revision="aaa001")

        engine = create_engine(url)
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
