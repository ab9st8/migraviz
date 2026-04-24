"""Tests for the Graphviz ER diagram renderer."""

import pytest

from sqlalchemy import (
    Column,
    ForeignKey,
    Integer,
    MetaData,
    String,
    Table,
)


def _make_metadata() -> MetaData:
    metadata = MetaData()
    Table(
        "users",
        metadata,
        Column("id", Integer, primary_key=True),
        Column("name", String(100), nullable=False),
        Column("email", String(255), nullable=True),
    )
    Table(
        "posts",
        metadata,
        Column("id", Integer, primary_key=True),
        Column("title", String(200), nullable=False),
        Column("author_id", Integer, ForeignKey("users.id"), nullable=False),
    )
    return metadata


def _make_schema_metadata() -> MetaData:
    metadata = MetaData()
    Table(
        "users",
        metadata,
        Column("id", Integer, primary_key=True),
        Column("name", String(100), nullable=False),
        schema="shared",
    )
    Table(
        "posts",
        metadata,
        Column("id", Integer, primary_key=True),
        Column("author_id", Integer, ForeignKey("shared.users.id"), nullable=False),
        schema="app",
    )
    return metadata


def test_metadata_to_graphviz_returns_digraph():
    """Should return a graphviz.Digraph object."""
    from migraviz.renderer import metadata_to_graphviz

    dot = metadata_to_graphviz(_make_metadata())

    import graphviz

    assert isinstance(dot, graphviz.Digraph)


def test_graphviz_contains_table_names():
    """The DOT source should contain table names."""
    from migraviz.renderer import metadata_to_graphviz

    dot = metadata_to_graphviz(_make_metadata())
    source = dot.source

    assert "users" in source
    assert "posts" in source


def test_graphviz_contains_columns():
    """The DOT source should contain column names."""
    from migraviz.renderer import metadata_to_graphviz

    dot = metadata_to_graphviz(_make_metadata())
    source = dot.source

    assert "name" in source
    assert "email" in source
    assert "title" in source
    assert "author_id" in source


def test_graphviz_contains_fk_edge():
    """Foreign keys should produce edges in the graph."""
    from migraviz.renderer import metadata_to_graphviz

    dot = metadata_to_graphviz(_make_metadata())
    source = dot.source

    # graphviz edge syntax: "posts":author_id -> "users":id
    assert "author_id" in source
    assert "->" in source


def test_graphviz_schema_qualified_names():
    """Schema-qualified table names should appear in the output."""
    from migraviz.renderer import metadata_to_graphviz

    dot = metadata_to_graphviz(_make_schema_metadata())
    source = dot.source

    assert "shared.users" in source
    assert "app.posts" in source


@pytest.mark.integration
def test_render_diagram_creates_file(tmp_path):
    """render_diagram should create an image file (requires graphviz system package)."""
    from migraviz.renderer import render_diagram

    output = tmp_path / "test.png"
    rendered = render_diagram(_make_metadata(), output, fmt="png")

    assert rendered.exists()
    assert rendered.suffix == ".png"
    assert rendered.stat().st_size > 0


@pytest.mark.integration
def test_render_diagram_svg(tmp_path):
    """render_diagram should support SVG output (requires graphviz system package)."""
    from migraviz.renderer import render_diagram

    output = tmp_path / "test.svg"
    rendered = render_diagram(_make_metadata(), output, fmt="svg")

    assert rendered.exists()
    assert rendered.suffix == ".svg"
    content = rendered.read_text()
    assert "<svg" in content
