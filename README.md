# migraviz

Generate ER diagrams from Alembic migration history.

Point migraviz at your `alembic.ini`, pick a revision, and get a DBML schema showing the state of your database at that point in time. Or point it at an existing database and just introspect.

## How it works

**Ephemeral mode:** spins up a temporary Postgres container, replays your Alembic migrations to the target revision, introspects the schema, outputs DBML.

**External DB mode:** connects to an existing database, introspects, outputs DBML. No migrations are run — useful in CI where a database already exists.

## Installation

```bash
uv add migraviz
```

Ephemeral mode requires Docker. External DB mode has no extra requirements.

## Usage

### Ephemeral mode

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

Multi-schema / multi-tenant:

```bash
migraviz ./alembic.ini \
  -s shared-schema -s tenant-schema \
  --schema shared --schema tenant_migraviz \
  -x tenant-schema=schema_name=tenant_migraviz
```

### External DB mode

Connect to an existing database and introspect it directly:

```bash
migraviz --db-url postgresql://user:pass@localhost:5432/mydb
```

With named schemas:

```bash
migraviz --db-url postgresql://user:pass@localhost:5432/mydb \
  --schema shared --schema tenant_foo
```

This is ideal for CI pipelines where a test database already exists after running migrations as part of the normal test setup.

## Requirements

- Python 3.13+
- Docker (ephemeral mode only)
