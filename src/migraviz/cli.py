"""CLI entrypoint — wired up in later commits."""

import click


@click.command()
def main() -> None:
    """Generate an ER diagram from Alembic migrations."""
    click.echo("migraviz — not yet implemented")
