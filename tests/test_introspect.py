"""Tests for schema introspection from a live DB."""

from pathlib import Path

import pytest


@pytest.mark.integration
def test_introspect_returns_tables(alembic_ini: Path, pg_url: str):
    """Introspecting after migration should return our tables."""
    from migraviz.introspect import introspect_schema
    from migraviz.migrate import run_migrations

    run_migrations(alembic_ini, pg_url, revision="head")
    metadata = introspect_schema(pg_url)

    table_names = set(metadata.tables.keys())
    assert "users" in table_names
    assert "posts" in table_names
    assert "alembic_version" not in table_names


@pytest.mark.integration
def test_introspect_columns(alembic_ini: Path, pg_url: str):
    """Introspected tables should have the right columns."""
    from migraviz.introspect import introspect_schema
    from migraviz.migrate import run_migrations

    run_migrations(alembic_ini, pg_url, revision="head")
    metadata = introspect_schema(pg_url)

    users = metadata.tables["users"]
    col_names = {c.name for c in users.columns}
    assert "id" in col_names
    assert "name" in col_names
    assert "email" in col_names

    id_col = users.c.id
    assert id_col.primary_key is True

    name_col = users.c.name
    assert name_col.nullable is False


@pytest.mark.integration
def test_introspect_foreign_keys(alembic_ini: Path, pg_url: str):
    """Introspected schema should include foreign key relationships."""
    from migraviz.introspect import introspect_schema
    from migraviz.migrate import run_migrations

    run_migrations(alembic_ini, pg_url, revision="head")
    metadata = introspect_schema(pg_url)

    posts = metadata.tables["posts"]
    fk_constraints = list(posts.foreign_key_constraints)
    assert len(fk_constraints) >= 1

    fk = fk_constraints[0]
    assert fk.referred_table.name == "users"
    assert "author_id" in {c.name for c in fk.columns}
