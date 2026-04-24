"""Ephemeral Postgres container for migration replay."""

from __future__ import annotations

from contextlib import contextmanager
from collections.abc import Generator

from testcontainers.postgres import PostgresContainer


@contextmanager
def ephemeral_pg() -> Generator[str]:
    """Spin up a throwaway Postgres, yield the connection URL, tear it down."""
    with PostgresContainer("postgres:16-alpine") as pg:
        yield pg.get_connection_url()
