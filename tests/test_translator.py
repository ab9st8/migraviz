"""Tests for SQLAlchemy MetaData -> DBML translation."""

from sqlalchemy import (
    Column,
    ForeignKey,
    Integer,
    MetaData,
    String,
    Table,
    Boolean,
)


def _make_simple_metadata() -> MetaData:
    """Build a minimal MetaData with one table for testing."""
    metadata = MetaData()
    Table(
        "users",
        metadata,
        Column("id", Integer, primary_key=True),
        Column("name", String(100), nullable=False),
        Column("email", String(255), nullable=True),
    )
    return metadata


def _make_metadata_with_fk() -> MetaData:
    """Build MetaData with two tables and a foreign key."""
    metadata = MetaData()
    Table(
        "users",
        metadata,
        Column("id", Integer, primary_key=True),
        Column("name", String(100), nullable=False),
    )
    Table(
        "posts",
        metadata,
        Column("id", Integer, primary_key=True),
        Column("title", String(200), nullable=False),
        Column("author_id", Integer, ForeignKey("users.id"), nullable=False),
        Column("published", Boolean, default=False),
    )
    return metadata


def test_single_table_produces_valid_dbml():
    """A single table should translate to a DBML Table block."""
    from migraviz.translator import metadata_to_dbml

    metadata = _make_simple_metadata()
    dbml = metadata_to_dbml(metadata)

    assert "Table users {" in dbml
    assert "id integer [pk]" in dbml
    assert "name varchar(100) [not null]" in dbml
    assert "email varchar(255)" in dbml


def test_foreign_key_produces_ref():
    """Foreign keys should produce DBML Ref lines."""
    from migraviz.translator import metadata_to_dbml

    metadata = _make_metadata_with_fk()
    dbml = metadata_to_dbml(metadata)

    assert "Table users {" in dbml
    assert "Table posts {" in dbml
    # DBML ref syntax: Ref: posts.author_id > users.id
    assert "Ref: posts.author_id > users.id" in dbml


def test_primary_key_annotation():
    """Primary key columns should have [pk] annotation."""
    from migraviz.translator import metadata_to_dbml

    metadata = _make_simple_metadata()
    dbml = metadata_to_dbml(metadata)

    assert "[pk]" in dbml


def test_not_null_annotation():
    """Non-nullable columns should have [not null] annotation."""
    from migraviz.translator import metadata_to_dbml

    metadata = _make_metadata_with_fk()
    dbml = metadata_to_dbml(metadata)

    # title is not null
    assert "title varchar(200) [not null]" in dbml
