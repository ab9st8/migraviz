"""Translate SQLAlchemy MetaData into DBML format."""

from __future__ import annotations

from sqlalchemy import MetaData


def metadata_to_dbml(metadata: MetaData) -> str:
    """Convert reflected MetaData to a DBML string."""
    parts: list[str] = []

    for table in sorted(metadata.tables.values(), key=lambda t: _full_name(t)):
        parts.append(_table_to_dbml(table))

    # Collect all foreign keys across tables
    refs = []
    for table in metadata.tables.values():
        for fk_constraint in table.foreign_key_constraints:
            for fk in fk_constraint.elements:
                refs.append(
                    f"Ref: {_full_name(table)}.{fk.parent.name} > "
                    f"{_full_name(fk.column.table)}.{fk.column.name}"
                )

    if refs:
        parts.append("")
        parts.extend(refs)

    return "\n".join(parts) + "\n"


def _full_name(table) -> str:
    """Return schema-qualified name if the table has a schema, otherwise just the name."""
    if table.schema:
        return f"{table.schema}.{table.name}"
    return table.name


def _table_to_dbml(table) -> str:
    """Convert a single SA Table to a DBML Table block."""
    lines = [f"Table {_full_name(table)} {{"]
    for col in table.columns:
        lines.append(f"  {_column_to_dbml(col)}")
    lines.append("}")
    return "\n".join(lines)


def _column_to_dbml(col) -> str:
    """Convert a SA Column to a DBML column line."""
    col_type = _format_type(col.type)
    annotations: list[str] = []

    if col.primary_key:
        annotations.append("pk")
    elif not col.nullable:
        annotations.append("not null")

    suffix = f" [{', '.join(annotations)}]" if annotations else ""
    return f"{col.name} {col_type}{suffix}"


def _format_type(sa_type) -> str:
    """Get a readable string for a SQLAlchemy column type."""
    try:
        return str(sa_type.compile())
    except Exception:
        return type(sa_type).__name__
