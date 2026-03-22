# Developer Guide

## Runtime Overview

- Backend: FastAPI + SQLModel
- UI: Jinja templates + static assets
- Auth: Cookie-based JWT and organization-scoped actor context

## Core Areas

- API routes: `src/foundry/api/routes/`
- UI router: `src/foundry/api/routes/ui.py`
- UI templates: `src/foundry/ui/templates/`
- Static assets: `src/foundry/ui/static/`

## Detailed Developer Docs

- [Integrations](integrations.md)
- [Documentation Architecture](docs-architecture.md)
