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


def _table_label(
    table,
    *,
    text_color: str = "#1a1a1a",
    type_color: str = "#888888",
    border_color: str = "#cccccc",
    header_bg: str = "#4a86c8",
) -> str:
    """Build an HTML-like label for a graphviz record node."""
    # Header row with table name
    header = (
        f'<TR><TD COLSPAN="3" BGCOLOR="{header_bg}">'
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
            f'<TD ALIGN="LEFT" PORT="{col.name}"><FONT COLOR="{text_color}">{col.name}{nullable}</FONT></TD>'
            f'<TD ALIGN="LEFT"><FONT COLOR="{type_color}">{col_type}</FONT></TD>'
            f'<TD ALIGN="RIGHT">{badge_str}</TD>'
            f"</TR>"
        )

    body = "".join(rows)
    return f'<<TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0" COLOR="{border_color}">{header}{body}</TABLE>>'


def metadata_to_graphviz(metadata: MetaData, *, dark: bool = False):
    """Convert reflected MetaData to a graphviz.Digraph object.

    Args:
        dark: Use dark color scheme (light text on dark background).
              Default is light mode (dark text on white background).

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

    if dark:
        bg_color = "#1e1e1e"
        text_color = "#d4d4d4"
        type_color = "#808080"
        border_color = "#444444"
        edge_color = "#888888"
        header_bg = "#3a6ea5"
    else:
        bg_color = "white"
        text_color = "#1a1a1a"
        type_color = "#888888"
        border_color = "#cccccc"
        edge_color = "#666666"
        header_bg = "#4a86c8"

    dot = graphviz.Digraph(
        "ER",
        graph_attr={
            "rankdir": "LR",
            "fontname": "Helvetica",
            "bgcolor": bg_color,
            "pad": "0.5",
            "nodesep": "0.8",
            "ranksep": "1.2",
            "splines": "ortho",
        },
        node_attr={
            "shape": "plaintext",
            "fontname": "Helvetica",
            "fontsize": "11",
        },
        edge_attr={
            "fontname": "Helvetica",
            "fontsize": "9",
            "color": edge_color,
            "arrowsize": "0.8",
        },
    )

    # Add table nodes
    for table in sorted(metadata.tables.values(), key=lambda t: _full_name(t)):
        dot.node(
            _full_name(table),
            label=_table_label(table, text_color=text_color,
                               type_color=type_color, border_color=border_color,
                               header_bg=header_bg),
        )

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
    *,
    dark: bool = False,
) -> Path:
    """Render an ER diagram to a file.

    fmt: graphviz output format — 'png', 'svg', 'pdf', etc.
    dark: use dark color scheme.
    Returns the path to the rendered file.
    """
    dot = metadata_to_graphviz(metadata, dark=dark)

    # graphviz renders to output_path + ".png" (appends extension),
    # so we strip the suffix to get the right filename
    stem = str(output.with_suffix(""))
    dot.render(stem, format=fmt, cleanup=True)

    rendered = Path(f"{stem}.{fmt}")
    return rendered
