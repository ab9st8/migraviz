"""In-memory schema representation, populated via SQLAlchemy introspection."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Column:
    name: str
    type: str
    nullable: bool = True
    primary_key: bool = False


@dataclass
class ForeignKey:
    constrained_table: str
    constrained_columns: list[str]
    referred_table: str
    referred_columns: list[str]
    name: str | None = None


@dataclass
class Table:
    name: str
    columns: dict[str, Column] = field(default_factory=dict)


@dataclass
class Schema:
    """Schema state introspected from a real database."""

    tables: dict[str, Table] = field(default_factory=dict)
    foreign_keys: list[ForeignKey] = field(default_factory=list)
