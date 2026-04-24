"""Run alembic migrations against a target database."""

from __future__ import annotations

from pathlib import Path

from alembic import command
from alembic.config import Config


def run_migrations(alembic_ini: Path, db_url: str, revision: str = "head") -> None:
    """Run alembic upgrade to the given revision against db_url.

    alembic_ini should point to the alembic.ini file. The sqlalchemy.url
    is overridden in memory so the original file is never modified.
    """
    config = Config(str(alembic_ini))

    # Resolve script_location relative to the ini file's directory,
    # since alembic expects it relative to where it's invoked from.
    script_location = config.get_main_option("script_location")
    if script_location and not Path(script_location).is_absolute():
        resolved = (alembic_ini.parent / script_location).resolve()
        config.set_main_option("script_location", str(resolved))

    config.set_main_option("sqlalchemy.url", db_url)
    command.upgrade(config, revision)
