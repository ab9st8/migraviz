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
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
)
@click.option(
    "-r",
    "--revision",
    default="head",
    help="Target Alembic revision (default: head).",
)
@click.option(
    "-o",
    "--output",
    type=click.Path(dir_okay=False, path_type=Path),
    default=None,
    help="Output file path. Prints to stdout if omitted.",
)
@click.option(
    "-s",
    "--section",
    "sections",
    multiple=True,
    default=("alembic",),
    help=(
        "Alembic ini section(s) to run. Repeat for multi-schema setups, "
        "e.g. -s alembic:shared -s alembic:tenant. Defaults to 'alembic'."
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
        "Extra -x arguments passed to alembic, in the form section:key=value. "
        "e.g. -x alembic:tenant:schema_name=tenant_migraviz"
    ),
)
def main(
    alembic_ini: Path,
    revision: str,
    output: Path | None,
    sections: tuple[str, ...],
    schemas: tuple[str, ...],
    x_args: tuple[str, ...],
) -> None:
    """Generate a DBML schema from Alembic migrations.

    ALEMBIC_INI is the path to your project's alembic.ini file.
    """
    # Parse -x args into per-section buckets: {section: [key=value, ...]}
    section_x_args: dict[str, list[str]] = {}
    for x_arg in x_args:
        # format: section:key=value
        parts = x_arg.split(":", maxsplit=2)
        if len(parts) == 3:
            sec = f"{parts[0]}:{parts[1]}"  # e.g. "alembic:tenant"
            section_x_args.setdefault(sec, []).append(parts[2])
        else:
            click.echo(f"Invalid -x format: {x_arg!r} (expected section:key=value)", err=True)
            sys.exit(1)

    click.echo("Spinning up ephemeral Postgres...", err=True)

    with ephemeral_pg() as db_url:
        # Create any requested schemas before running migrations
        if schemas:
            engine = create_engine(db_url)
            with engine.connect() as conn:
                for schema in schemas:
                    conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema}"))
                conn.commit()
            engine.dispose()

        for section in sections:
            click.echo(f"Running migrations [{section}] to '{revision}'...", err=True)
            run_migrations(
                alembic_ini,
                db_url,
                revision=revision,
                section=section,
                x_args=section_x_args.get(section),
            )

        click.echo("Introspecting schema...", err=True)
        metadata = introspect_schema(
            db_url, schemas=list(schemas) if schemas else None,
        )

    if not metadata.tables:
        click.echo("No tables found after migration.", err=True)
        sys.exit(1)

    dbml = metadata_to_dbml(metadata)

    if output:
        output.write_text(dbml)
        click.echo(f"Written to {output}", err=True)
    else:
        click.echo(dbml)
