# Module Map

This page maps major source areas to responsibility.

## Core Runtime

- `src/foundry/api/main.py` - app startup, route registration, static mounts, health endpoint.
- `src/foundry/settings.py` - typed configuration surface for all `FORGE_*` variables.
- `src/foundry/db.py` - engine lifecycle, startup schema init, fallback logic.

## API Routes

- `src/foundry/api/routes/auth.py` - token issuance.
- `src/foundry/api/routes/ui.py` - server-rendered UI routes and form handlers.
- `src/foundry/api/routes/*.py` - domain API modules (clients, projects, quests, assets, reviews, templates, timeline, files, todos, kpis, snapshots, integrations).

## Models and Schemas

- `src/foundry/models.py` - SQLModel entities and enums.
- `src/foundry/schemas.py` - API schema layer.

## Services

- `src/foundry/services/` - business logic helpers (activity logging, template seeding, domain services).

## Integrations

- `src/foundry/integrations/` - Celonis and GitLab integration adapters.

## UI Surface

- `src/foundry/ui/templates/` - Jinja templates for route-level pages.
- `src/foundry/ui/static/` - CSS and static assets.

## Data Evolution

- `alembic/versions/` - migration history.
- `alembic/env.py` - migration runtime config.

## Build and Packaging

- `Dockerfile` and `docker-compose.yml` - containerized runtime.
- `FoundryDesktop.spec` - desktop packaging.
- `scripts/*.ps1` - build and operational helper scripts.

## Documentation System

- `mkdocs.yml` - site navigation/theme/build config.
- `site_docs/` - canonical docs source.
- `docs_site/` - generated static docs output.
- `tests/test_docs_site_routes.py` - docs route/redirect regression checks.
