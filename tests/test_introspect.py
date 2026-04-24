"""Tests for schema introspection from a live DB."""

from pathlib import Path

import pytest


@pytest.mark.integration
def test_introspect_returns_tables(alembic_ini: Path):
    """Introspecting after migration should return our tables."""
    from migraviz.db import ephemeral_pg
    from migraviz.introspect import introspect_schema
    from migraviz.migrate import run_migrations

    with ephemeral_pg() as url:
        run_migrations(alembic_ini, url, revision="head")
        metadata = introspect_schema(url)

    table_names = set(metadata.tables.keys())
    assert "users" in table_names
    assert "posts" in table_names
    assert "alembic_version" not in table_names


@pytest.mark.integration
def test_introspect_columns(alembic_ini: Path):
    """Introspected tables should have the right columns."""
    from migraviz.db import ephemeral_pg
    from migraviz.introspect import introspect_schema
    from migraviz.migrate import run_migrations

    with ephemeral_pg() as url:
        run_migrations(alembic_ini, url, revision="head")
        metadata = introspect_schema(url)

    users = metadata.tables["users"]
    assert "id" in users.columns
    assert "name" in users.columns
    assert "email" in users.columns
    assert users.columns["id"].primary_key is True
    assert users.columns["name"].nullable is False


@pytest.mark.integration
def test_introspect_foreign_keys(alembic_ini: Path):
    """Introspected schema should include foreign key relationships."""
    from migraviz.db import ephemeral_pg
    from migraviz.introspect import introspect_schema
    from migraviz.migrate import run_migrations

    with ephemeral_pg() as url:
        run_migrations(alembic_ini, url, revision="head")
        metadata = introspect_schema(url)

    assert len(metadata.foreign_keys) >= 1
    fk = metadata.foreign_keys[0]
    assert fk.constrained_table == "posts"
    assert fk.referred_table == "users"
    assert "author_id" in fk.constrained_columns
