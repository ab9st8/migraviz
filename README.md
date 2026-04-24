# migraviz

Generate ER diagrams from Alembic migration history.

Point migraviz at your Alembic migrations directory, pick a revision, and get a DBML schema (or a rendered diagram) showing the state of your database at that point in time.

## How it works

1. Spins up an ephemeral Postgres container via testcontainers
2. Replays your Alembic migrations up to the target revision
3. Introspects the resulting schema with SQLAlchemy
4. Outputs DBML (or renders an image)

## Installation

```bash
uv add migraviz
```

## Usage

```bash
migraviz ./alembic/versions --revision head
```

## Requirements

- Python 3.13+
- Docker (for the ephemeral Postgres container)
