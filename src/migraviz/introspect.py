"""Introspect a live database via SQLAlchemy and return a Schema."""

from __future__ import annotations

from sqlalchemy import MetaData, create_engine

from migraviz.models import Column, ForeignKey, Schema, Table


def introspect_schema(db_url: str) -> Schema:
    """Connect to a database and reflect its full schema into our model."""
    engine = create_engine(db_url)
    metadata = MetaData()
    metadata.reflect(bind=engine)

    schema = Schema()

    for table_name, sa_table in metadata.tables.items():
        if table_name == "alembic_version":
            continue

        table = Table(name=table_name)
        for sa_col in sa_table.columns:
            table.columns[sa_col.name] = Column(
                name=sa_col.name,
                type=_format_type(sa_col.type),
                nullable=sa_col.nullable,
                primary_key=sa_col.primary_key,
            )
        schema.tables[table_name] = table

    for table_name, sa_table in metadata.tables.items():
        if table_name == "alembic_version":
            continue
        for fk_constraint in sa_table.foreign_key_constraints:
            schema.foreign_keys.append(
                ForeignKey(
                    name=fk_constraint.name,
                    constrained_table=table_name,
                    constrained_columns=[c.name for c in fk_constraint.columns],
                    referred_table=fk_constraint.referred_table.name,
                    referred_columns=[
                        e.column.name for e in fk_constraint.elements
                    ],
                )
            )

    engine.dispose()
    return schema


def _format_type(sa_type) -> str:
    """Get a readable string for a SQLAlchemy column type."""
    try:
        return str(sa_type.compile())
    except Exception:
        return type(sa_type).__name__
