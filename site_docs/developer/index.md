# Developer Guide

This section explains how to build, test, and extend the application safely.

## Start Here

1. [Local Development](local-development.md)
2. [Architecture](architecture.md)
3. [Data Models and Migrations](data-models-and-migrations.md)
4. [Auth and Access Control](auth-and-access-control.md)
5. [Testing](testing.md)

## Domain-Specific Pages

- [Integrations](integrations.md)
- [Documentation Architecture](docs-architecture.md)

## Key Source Areas

- `src/foundry/api/main.py`
- `src/foundry/api/routes/`
- `src/foundry/models.py`
- `src/foundry/services/`
- `src/foundry/settings.py`
- `src/foundry/db.py`

## Contribution Rule of Thumb

Any user-visible change should update:

1. Route/service tests.
2. Relevant `site_docs/` pages.
3. MkDocs navigation when introducing a new durable doc section.
