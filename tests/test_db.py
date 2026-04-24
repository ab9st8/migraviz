"""Tests for the ephemeral Postgres setup."""

import pytest
from sqlalchemy import create_engine, text


@pytest.mark.integration
def test_pg_yields_working_url(pg_url: str):
    """The fixture should yield a URL we can connect to and query."""
    engine = create_engine(pg_url)
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        assert result.scalar() == 1
    engine.dispose()


@pytest.mark.integration
def test_pg_is_clean(pg_url: str):
    """Each test database should start with no user tables."""
    engine = create_engine(pg_url)
    with engine.connect() as conn:
        result = conn.execute(
            text(
                "SELECT count(*) FROM information_schema.tables "
                "WHERE table_schema = 'public'"
            )
        )
        assert result.scalar() == 0
    engine.dispose()
