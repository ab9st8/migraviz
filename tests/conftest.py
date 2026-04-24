"""Shared fixtures for migraviz tests."""

from pathlib import Path

import pytest

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def alembic_dir() -> Path:
    """Path to the test fixture alembic directory."""
    return FIXTURES_DIR / "alembic"


@pytest.fixture
def alembic_ini() -> Path:
    """Path to the test fixture alembic.ini."""
    return FIXTURES_DIR / "alembic.ini"
