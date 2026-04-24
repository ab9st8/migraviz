# migraviz

Generate ER diagrams from Alembic migration history.

Point migraviz at your `alembic.ini`, pick a revision, and get a DBML schema showing the state of your database at that point in time.

## How it works

1. Spins up an ephemeral Postgres container via testcontainers
2. Replays your Alembic migrations up to the target revision
3. Introspects the resulting schema with SQLAlchemy
4. Outputs DBML

## Installation

```bash
uv add migraviz
```

Requires Docker to be running (for the ephemeral Postgres container).

## Usage

Basic — single alembic section, public schema:

```bash
migraviz ./alembic.ini
```

Specific revision:

```bash
migraviz ./alembic.ini -r abc123
```

Write to a file instead of stdout:

```bash
migraviz ./alembic.ini -o schema.dbml
```

### Multi-schema / multi-tenant

For projects with multiple alembic sections and named Postgres schemas:

```bash
migraviz ./alembic.ini \
  -s alembic:shared -s alembic:tenant \
  --schema shared --schema tenant_migraviz \
  -x alembic:tenant:schema_name=tenant_migraviz
```

This will:
- Create the `shared` and `tenant_migraviz` schemas in the ephemeral database
- Run migrations from the `alembic:shared` section
- Run migrations from the `alembic:tenant` section, passing `-x schema_name=tenant_migraviz` so the tenant env.py targets the right schema
- Reflect both schemas and output DBML with schema-qualified table names

## Requirements

- Python 3.13+
- Docker
