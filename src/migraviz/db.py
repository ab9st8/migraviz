"""Ephemeral Postgres container for migration replay."""

from __future__ import annotations

import subprocess
import time
import uuid
from contextlib import contextmanager
from collections.abc import Generator

from sqlalchemy import create_engine, text

PG_IMAGE = "postgres:16-alpine"
PG_USER = "migraviz"
PG_PASS = "migraviz"
PG_DB = "migraviz"


@contextmanager
def ephemeral_pg(port: int = 15433) -> Generator[str]:
    """Spin up a throwaway Postgres, yield the connection URL, tear it down.

    Uses a fixed port binding to avoid dynamic port mapping issues
    with colima and similar Docker VM setups.
    """
    container_name = f"migraviz-ephemeral-{uuid.uuid4().hex[:8]}"
    url = (
        f"postgresql+psycopg2://{PG_USER}:{PG_PASS}"
        f"@localhost:{port}/{PG_DB}"
    )

    subprocess.run(
        [
            "docker", "run", "-d",
            "--name", container_name,
            "-p", f"{port}:5432",
            "-e", f"POSTGRES_USER={PG_USER}",
            "-e", f"POSTGRES_PASSWORD={PG_PASS}",
            "-e", f"POSTGRES_DB={PG_DB}",
            PG_IMAGE,
        ],
        check=True,
        capture_output=True,
    )

    try:
        for _ in range(30):
            try:
                engine = create_engine(url)
                with engine.connect() as conn:
                    conn.execute(text("SELECT 1"))
                engine.dispose()
                break
            except Exception:
                time.sleep(1)
        else:
            raise RuntimeError("Postgres container didn't become ready in 30s")

        yield url
    finally:
        subprocess.run(
            ["docker", "rm", "-f", container_name],
            capture_output=True,
        )
