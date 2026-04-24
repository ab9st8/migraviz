"""Introspect a live database via SQLAlchemy."""

from __future__ import annotations

from sqlalchemy import MetaData, create_engine


def introspect_schema(db_url: str) -> MetaData:
    """Connect to a database and reflect its schema.

    Returns a SQLAlchemy MetaData with all tables reflected.
    The alembic_version bookkeeping table is removed.
    """
    engine = create_engine(db_url)
    metadata = MetaData()
    metadata.reflect(bind=engine)
    engine.dispose()

    # Drop alembic's own table so it doesn't show up in output
    if "alembic_version" in metadata.tables:
        metadata.remove(metadata.tables["alembic_version"])

    return metadata
