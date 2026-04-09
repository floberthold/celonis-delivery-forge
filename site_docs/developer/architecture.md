# Architecture

This page summarizes core runtime architecture and boundaries.

## High-Level Stack

- FastAPI application with modular routers.
- SQLModel models for persistence.
- Jinja templates for UI pages.
- JWT-based authentication for API and UI session flows.

## Core Modules

- `src/foundry/api/main.py`: app wiring, route inclusion, static mounts.
- `src/foundry/api/routes/`: domain routers and UI routes.
- `src/foundry/models.py`: enums and SQLModel entities.
- `src/foundry/services/`: domain/business logic helpers.
- `src/foundry/db.py`: engine lifecycle, startup initialization, fallback logic.
- `src/foundry/settings.py`: `FORGE_*` configuration surface.

## Request Flow

1. Request enters FastAPI route.
2. Dependency injection resolves current session/actor.
3. Route validates scope and input.
4. Service operations and persistence updates run.
5. Activity logging is written for key actions.
6. API response or template response is returned.

## Multi-Tenant Scoping Model

- Organization membership gates access.
- Auth tokens can include selected organization context.
- UI and API routes should consistently enforce org-bound access.

## Documentation Surface

- Canonical docs source: `site_docs/`.
- Built docs output: `docs_site/`.
- Runtime mount path: `/docs-site`.
- Legacy `/docu/*` routes redirect to new docs-site pages.
