"""CLI entrypoint for migraviz."""

from __future__ import annotations

import sys
from pathlib import Path

import click
from sqlalchemy import create_engine, text

from migraviz.db import ephemeral_pg
from migraviz.introspect import introspect_schema
from migraviz.migrate import run_migrations
from migraviz.translator import metadata_to_dbml


@click.command()
@click.argument(
    "alembic_ini",
    required=False,
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
)
@click.option(
    "--db-url",
    default=None,
    help=(
        "Connect to an existing database instead of spinning up an ephemeral one. "
        "Skips migrations entirely — just introspects and outputs DBML. "
        "Mutually exclusive with ALEMBIC_INI."
    ),
)
@click.option(
    "-r",
    "--revision",
    default="head",
    help="Target Alembic revision (default: head). Only used in ephemeral mode.",
)
@click.option(
    "-o",
    "--output",
    type=click.Path(dir_okay=False, path_type=Path),
    default=None,
    help="Output file path. Prints to stdout if omitted (DBML only).",
)
@click.option(
    "-f",
    "--format",
    "fmt",
    type=click.Choice(["dbml", "png", "svg", "pdf"]),
    default="dbml",
    help="Output format (default: dbml). Image formats require graphviz.",
)
@click.option(
    "-s",
    "--section",
    "sections",
    multiple=True,
    default=("alembic",),
    help=(
        "Alembic ini section(s) to run. Repeat for multi-schema setups, "
        "e.g. -s alembic:shared -s alembic:tenant. Defaults to 'alembic'. "
        "Only used in ephemeral mode."
    ),
)
@click.option(
    "--schema",
    "schemas",
    multiple=True,
    help=(
        "Postgres schema(s) to reflect. Repeat for multiple, "
        "e.g. --schema shared --schema tenant_migraviz. "
        "If omitted, reflects the default (public) schema."
    ),
)
@click.option(
    "-x",
    "x_args",
    multiple=True,
    help=(
        "Extra -x arguments passed to a specific alembic section. "
        "Format: section=key=value. "
        "e.g. -x tenant-schema=schema_name=tenant_migraviz. "
        "Only used in ephemeral mode."
    ),
)
def main(
    alembic_ini: Path | None,
    db_url: str | None,
    revision: str,
    output: Path | None,
    fmt: str,
    sections: tuple[str, ...],
    schemas: tuple[str, ...],
    x_args: tuple[str, ...],
) -> None:
    """Generate a DBML schema or ER diagram from Alembic migrations.

    \b
    Ephemeral mode (default):
      migraviz ./alembic.ini [-r revision]
      Spins up a temporary Postgres, runs migrations, introspects.

    \b
    External DB mode:
      migraviz --db-url postgresql://user:pass@host:port/db [--schema ...]
      Connects to an existing database, introspects.
      No migrations are run — the database should already be in the desired state.
    """
    if db_url and alembic_ini:
        click.echo("Cannot use both --db-url and ALEMBIC_INI.", err=True)
        sys.exit(1)

    if not db_url and not alembic_ini:
        click.echo("Provide either ALEMBIC_INI or --db-url.", err=True)
        sys.exit(1)

    if fmt != "dbml" and not output:
        click.echo(f"--output is required for {fmt} format.", err=True)
        sys.exit(1)

    if db_url:
        metadata = _introspect_external(db_url, schemas)
    else:
        assert alembic_ini is not None
        metadata = _run_ephemeral(alembic_ini, revision, sections, schemas, x_args)

    if not metadata.tables:
        click.echo("No tables found.", err=True)
        sys.exit(1)

    if fmt == "dbml":
        dbml = metadata_to_dbml(metadata)
        if output:
            output.write_text(dbml)
            click.echo(f"Written to {output}", err=True)
        else:
            click.echo(dbml)
    else:
        from migraviz.renderer import render_diagram

        assert output is not None
        try:
            rendered = render_diagram(metadata, output, fmt=fmt)
            click.echo(f"Rendered to {rendered}", err=True)
        except ImportError as e:
            click.echo(str(e), err=True)
            sys.exit(1)


def _introspect_external(db_url, schemas):
    """External DB mode: just connect and reflect."""
    click.echo("Introspecting schema...", err=True)
    return introspect_schema(
        db_url, schemas=list(schemas) if schemas else None,
    )


def _run_ephemeral(alembic_ini, revision, sections, schemas, x_args):
    """Ephemeral mode: spin up postgres, migrate, introspect."""
    # Parse -x args into per-section buckets: {section: [key=value, ...]}
    # Format: section=key=value (first = separates section from the rest)
    section_x_args: dict[str, list[str]] = {}
    for x_arg in x_args:
        parts = x_arg.split("=", maxsplit=1)
        if len(parts) == 2 and parts[0] and parts[1]:
            section_x_args.setdefault(parts[0], []).append(parts[1])
        else:
            click.echo(
                f"Invalid -x format: {x_arg!r} (expected section=key=value)",
                err=True,
            )
            sys.exit(1)

    click.echo("Spinning up ephemeral Postgres...", err=True)

    with ephemeral_pg() as url:
        if schemas:
            engine = create_engine(url)
            with engine.connect() as conn:
                for schema in schemas:
                    conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema}"))
                conn.commit()
            engine.dispose()

        for section in sections:
            click.echo(f"Running migrations [{section}] to '{revision}'...", err=True)
            run_migrations(
                alembic_ini,
                url,
                revision=revision,
                section=section,
                x_args=section_x_args.get(section),
            )

        click.echo("Introspecting schema...", err=True)
        metadata = introspect_schema(
            url, schemas=list(schemas) if schemas else None,
        )

    return metadata
