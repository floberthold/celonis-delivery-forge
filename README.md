# Celonis Delivery Forge

Celonis implementations should not be crafted in isolation. The Delivery Foundry establishes a dual-control governance framework for multi-tenant Celonis projects.

Every asset is forged. Every change is reviewed. Nothing reaches production without two hammers.

Built for consultants. Built for scale. Built to last.

## MVP Scope

- Project and client registry
- Asset ownership and membership tracking
- 4-eyes review flow (`submit -> approve/request changes`)
- Timeline view for project and asset activity
- Topic pages with inline create/edit/delete for projects, assets, reviews, people, clients, and timeline events
- Local accounts with JWT login
- Optional read-only Celonis import adapter (stub)
- Companion Celonis actions (connect, extract, import) from dashboard
- Extension-ready backend contracts and skeleton

## Tech Stack

- Python 3.11+
- FastAPI + SQLModel
- PostgreSQL
- Docker Compose for local services

## Quick Start (Local Python)

1. Copy environment variables:

	```powershell
	Copy-Item .env.example .env
	```

2. Install dependencies:

	```powershell
	python -m pip install --upgrade pip
	python -m pip install -e .
	```

3. Run API:

	```powershell
	uvicorn foundry.api.main:app --reload
	```

4. Open:

- Swagger: <http://127.0.0.1:8000/docs>
- Health: <http://127.0.0.1:8000/health>
- UI Dashboard: <http://127.0.0.1:8000/dashboard>
- User Docs: <http://127.0.0.1:8000/docu/user.html>
- Developer Docs: <http://127.0.0.1:8000/docu/developer.html>

Documentation source files for these pages are stored in the root `docu/` folder.
Reusable visual graphics for the docs are stored in `src/foundry/ui/static/docs/`.

5. Configure Celonis token for companion actions:

```powershell
$env:FORGE_CELONIS_API_TOKEN="<your-token>"
```

## Quick Start (Desktop Mode)

```powershell
python -m foundry.desktop.app
```

This starts the local API and opens the browser automatically.

## Standalone Windows App (No Terminal for runtime)

1. Build standalone `.exe` once:

```powershell
.\scripts\build_standalone.ps1
```

2. Start without terminal:

- Double-click `scripts/run_standalone.vbs` (hidden window, prefers `.venv\Scripts\pythonw.exe`)
- or double-click `scripts/run_standalone.bat` (tries EXE first, then `pythonw` fallback)
- or run `scripts/run_standalone_debug.bat` to keep output in the console for troubleshooting

This uses `dist/FoundryDesktop.exe` and does not require Docker or containers.
Desktop startup logs are written to `%LOCALAPPDATA%/CelonisDeliveryForge/desktop.log`.

## Quick Start (Docker)

```powershell
Copy-Item .env.example .env
docker compose up --build
```

## Core API Endpoints

- `POST /people/` create local person
- `POST /auth/token` login and receive JWT
- `POST /clients/` create client
- `POST /projects/` create project
- `POST /projects/{project_id}/memberships` assign colleagues
- `PATCH /projects/{project_id}/status` change project status with governance checks
- `POST /assets/` register asset
- `GET /assets/matrix` who is/was on which asset
- `POST /reviews/submit` submit change for review
- `POST /reviews/decision` approve or request changes
- `GET /timeline/` timeline by entity
- `POST /celonis/connections/upsert` upsert tenant-scoped Celonis connection
- `GET /celonis/connections` list configured Celonis connections
- `POST /celonis/extract` trigger API extract call for a client connection
- `POST /celonis/import` trigger API import call for a client connection

## Companion Workflow

- Open `/dashboard` and use the Celonis cards:
	- **Celonis Connection**: bind a `client` to a `tenant base URL`.
	- **Celonis Extract**: call a GET endpoint path on that tenant.
	- **Celonis Import**: call a POST endpoint path with JSON payload.
- Open `/tenant-ui` for multi-frame navigation and popup/new-tab fallback when embedding is blocked.

## Extension Preparation

- Skeleton lives in `extension/`:
	- `manifest.json`
	- `src/background.js`
	- `src/content.js`
- The skeleton is wired for future in-page buttons/overlays and is designed to call the existing `/celonis/*` backend contracts.

## Governance Rules (MVP)

- Author and reviewer must be different users.
- A review requires at least two active project memberships.
- Only assigned project members can submit/review.
- Project cannot move to active with fewer than 2 active memberships.
- Project cannot close while assets are still in review.
- Snippet-worthy is only allowed on approved reviews.

## Architecture Decision Record

- See `docs/adr/0001-mvp-architecture.md`

# Developers

Florian Berthold - 2026 - florian.d.berthold@gmail.com