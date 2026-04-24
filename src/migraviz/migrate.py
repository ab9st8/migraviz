"""Run alembic migrations against a target database."""

from __future__ import annotations

import argparse
from pathlib import Path

from alembic import command
from alembic.config import Config


def run_migrations(
    alembic_ini: Path,
    db_url: str,
    revision: str = "head",
    section: str = "alembic",
    x_args: list[str] | None = None,
) -> None:
    """Run alembic upgrade to the given revision against db_url.

    alembic_ini should point to the alembic.ini file. The sqlalchemy.url
    is overridden in memory so the original file is never modified.

    section: ini section name (e.g. 'alembic:shared', 'alembic:tenant').
    x_args: extra -x arguments (e.g. ['schema_name=tenant_migraviz']).
    """
    config = Config(str(alembic_ini), ini_section=section)

    # Resolve script_location relative to the ini file's directory,
    # since alembic expects it relative to where it's invoked from.
    script_location = config.get_main_option("script_location")
    if script_location and not Path(script_location).is_absolute():
        resolved = (alembic_ini.parent / script_location).resolve()
        config.set_main_option("script_location", str(resolved))

    config.set_main_option("sqlalchemy.url", db_url)

    # Wire up -x arguments so env.py can read them via context.get_x_argument()
    if x_args:
        config.cmd_opts = argparse.Namespace()
        config.cmd_opts.x = x_args
    else:
        config.cmd_opts = argparse.Namespace()
        config.cmd_opts.x = []

    command.upgrade(config, revision)
