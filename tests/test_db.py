"""Tests for the ephemeral Postgres context manager."""

import pytest
from sqlalchemy import create_engine, text


@pytest.mark.integration
def test_ephemeral_pg_yields_working_url():
    """The context manager should yield a URL we can connect to and query."""
    from migraviz.db import ephemeral_pg

    with ephemeral_pg() as url:
        engine = create_engine(url)
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            assert result.scalar() == 1
        engine.dispose()


@pytest.mark.integration
def test_ephemeral_pg_is_clean():
    """Each ephemeral DB should start with no user tables."""
    from migraviz.db import ephemeral_pg

    with ephemeral_pg() as url:
        engine = create_engine(url)
        with engine.connect() as conn:
            result = conn.execute(
                text(
                    "SELECT count(*) FROM information_schema.tables "
                    "WHERE table_schema = 'public'"
                )
            )
            assert result.scalar() == 0
        engine.dispose()
