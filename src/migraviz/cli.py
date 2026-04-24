"""CLI entrypoint for migraviz."""

from __future__ import annotations

import sys
from pathlib import Path

import click

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
def main(alembic_ini: Path, revision: str, output: Path | None) -> None:
    """Generate a DBML schema from Alembic migrations.

    ALEMBIC_INI is the path to your project's alembic.ini file.
    """
    click.echo(f"Spinning up ephemeral Postgres...", err=True)

    with ephemeral_pg() as db_url:
        click.echo(f"Running migrations to '{revision}'...", err=True)
        run_migrations(alembic_ini, db_url, revision=revision)

        click.echo("Introspecting schema...", err=True)
        metadata = introspect_schema(db_url)

    if not metadata.tables:
        click.echo("No tables found after migration.", err=True)
        sys.exit(1)

    dbml = metadata_to_dbml(metadata)

    if output:
        output.write_text(dbml)
        click.echo(f"Written to {output}", err=True)
    else:
        click.echo(dbml)
