"""Introspect a live database via SQLAlchemy."""

from __future__ import annotations

from sqlalchemy import MetaData, create_engine


def introspect_schema(db_url: str, schemas: list[str] | None = None) -> MetaData:
    """Connect to a database and reflect its schema.

    Returns a SQLAlchemy MetaData with all tables reflected.
    The alembic_version bookkeeping table is removed.

    schemas: list of postgres schema names to reflect (e.g. ['shared', 'tenant_migraviz']).
             If None, reflects the default (public) schema only.
    """
    engine = create_engine(db_url)
    metadata = MetaData()

    if schemas:
        for schema in schemas:
            metadata.reflect(bind=engine, schema=schema)
    else:
        metadata.reflect(bind=engine)

    engine.dispose()

    # Drop alembic's own tables so they don't show up in output
    alembic_tables = [
        t for t in metadata.tables.values() if t.name == "alembic_version"
    ]
    for t in alembic_tables:
        metadata.remove(t)

    return metadata
