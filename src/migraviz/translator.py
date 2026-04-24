"""Translate SQLAlchemy MetaData into DBML format."""

from __future__ import annotations

from sqlalchemy import MetaData


def metadata_to_dbml(metadata: MetaData) -> str:
    """Convert reflected MetaData to a DBML string."""
    parts: list[str] = []

    for table in sorted(metadata.tables.values(), key=lambda t: t.name):
        parts.append(_table_to_dbml(table))

    # Collect all foreign keys across tables
    refs = []
    for table in metadata.tables.values():
        for fk_constraint in table.foreign_key_constraints:
            for fk in fk_constraint.elements:
                refs.append(
                    f"Ref: {table.name}.{fk.parent.name} > "
                    f"{fk.column.table.name}.{fk.column.name}"
                )

    if refs:
        parts.append("")
        parts.extend(refs)

    return "\n".join(parts) + "\n"


def _table_to_dbml(table) -> str:
    """Convert a single SA Table to a DBML Table block."""
    lines = [f"Table {table.name} {{"]
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
