# Data Models and Migrations

This page describes schema ownership and migration discipline.

## Data Model Source

- SQLModel entities are defined in `src/foundry/models.py`.
- API request/response schemas are in `src/foundry/schemas.py`.

## Migration Tooling

- Alembic configuration is in `alembic/`.
- Migration files live in `alembic/versions/`.

## Safe Migration Workflow

1. Update model definitions.
2. Generate migration script.
3. Review generated SQL for destructive operations.
4. Apply migration in a test environment.
5. Run targeted regression tests.
6. Update docs for any user/admin visible changes.

## Startup Initialization Behavior

On startup, `init_db()`:

1. Initializes schema.
2. Applies sqlite legacy repair for missing project columns when needed.
3. Seeds default templates.
4. Falls back to local sqlite only when allowed by environment settings.

## Migration Validation Checklist

- Does `/health` show expected backend and startup mode?
- Do key CRUD routes still pass tests?
- Are new columns reflected in both API and UI behavior?
- Are fallback scenarios still safe in `dev`/`local`?
