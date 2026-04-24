"""Render SQLAlchemy MetaData as an ER diagram via Graphviz."""

from __future__ import annotations

from io import BytesIO
from pathlib import Path

from sqlalchemy import MetaData


def _full_name(table) -> str:
    if table.schema:
        return f"{table.schema}.{table.name}"
    return table.name


def _format_type(sa_type) -> str:
    try:
        return str(sa_type.compile())
    except Exception:
        return type(sa_type).__name__


def _table_label(table) -> str:
    """Build an HTML-like label for a graphviz record node."""
    # Header row with table name
    header = (
        f'<TR><TD COLSPAN="3" BGCOLOR="#4a86c8">'
        f'<FONT COLOR="white"><B>{_full_name(table)}</B></FONT>'
        f"</TD></TR>"
    )

    rows = []
    for col in table.columns:
        col_type = _format_type(col.type)

        badges = []
        if col.primary_key:
            badges.append('<FONT COLOR="#c8a84a">PK</FONT>')
        if col.foreign_keys:
            badges.append('<FONT COLOR="#8bc34a">FK</FONT>')

        badge_str = " ".join(badges)
        nullable = "" if col.nullable or col.primary_key else " •"

        rows.append(
            f"<TR>"
            f'<TD ALIGN="LEFT" PORT="{col.name}">{col.name}{nullable}</TD>'
            f'<TD ALIGN="LEFT"><FONT COLOR="#888888">{col_type}</FONT></TD>'
            f'<TD ALIGN="RIGHT">{badge_str}</TD>'
            f"</TR>"
        )

    body = "".join(rows)
    return f'<<TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0">{header}{body}</TABLE>>'


def metadata_to_graphviz(metadata: MetaData):
    """Convert reflected MetaData to a graphviz.Digraph object.

    Raises ImportError if the graphviz package is not installed.
    """
    try:
        import graphviz
    except ImportError:
        raise ImportError(
            "The 'graphviz' Python package is required for image output. "
            "Install it with: uv add graphviz\n"
            "You also need the Graphviz system package: "
            "brew install graphviz (macOS) or apt install graphviz (Linux)."
        )

    dot = graphviz.Digraph(
        "ER",
        graph_attr={
            "rankdir": "LR",
            "fontname": "Helvetica",
            "bgcolor": "transparent",
            "pad": "0.5",
            "nodesep": "0.8",
            "ranksep": "1.2",
        },
        node_attr={
            "shape": "plaintext",
            "fontname": "Helvetica",
            "fontsize": "11",
        },
        edge_attr={
            "fontname": "Helvetica",
            "fontsize": "9",
            "color": "#666666",
            "arrowsize": "0.8",
        },
    )

    # Add table nodes
    for table in sorted(metadata.tables.values(), key=lambda t: _full_name(t)):
        dot.node(_full_name(table), label=_table_label(table))

    # Add foreign key edges
    for table in metadata.tables.values():
        for fk_constraint in table.foreign_key_constraints:
            for fk in fk_constraint.elements:
                dot.edge(
                    f"{_full_name(table)}:{fk.parent.name}",
                    f"{_full_name(fk.column.table)}:{fk.column.name}",
                )

    return dot


def render_diagram(
    metadata: MetaData,
    output: Path,
    fmt: str = "png",
) -> Path:
    """Render an ER diagram to a file.

    fmt: graphviz output format — 'png', 'svg', 'pdf', etc.
    Returns the path to the rendered file.
    """
    dot = metadata_to_graphviz(metadata)

    # graphviz renders to output_path + ".png" (appends extension),
    # so we strip the suffix to get the right filename
    stem = str(output.with_suffix(""))
    dot.render(stem, format=fmt, cleanup=True)

    rendered = Path(f"{stem}.{fmt}")
    return rendered
