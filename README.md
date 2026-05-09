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

## 🚀 Quick Start

### Option 1: Auto-Startup (Recommended)

The easiest way to get running — one command:

**PowerShell:**
```powershell
.\START.ps1
```

**Command Prompt:**
```cmd
START.bat
```

The script will:
- ✅ Install dependencies automatically (if needed)
- ✅ Start the API server with auto-reload
- ✅ Server runs at `http://127.0.0.1:8000`
- ✅ Open the UI dashboard in your browser automatically (via desktop launcher)

**That's it!** Press `Ctrl+C` to stop.

### Option 2: Manual Startup

If you prefer to run commands yourself:

1. **Install dependencies** (one time only):

	```powershell
	python -m pip install --upgrade pip
	python -m pip install -e .
	```

2. **Start the server**:

	```powershell
	uvicorn foundry.api.main:app --reload
	```

3. **Open in browser**:
	- **UI Dashboard:** <http://127.0.0.1:8000>
	- **API Docs (Swagger):** <http://127.0.0.1:8000/docs>
	- **Health Check:** <http://127.0.0.1:8000/health>

### Database

The default local profile uses **SQLite** — no external database needed!
- Local database: `AppData\Local\CelonisDeliveryForge\foundry.db`
- The app boots instantly without waiting for PostgreSQL

If you want startup to fail instead of falling back to SQLite, set:
```powershell
$env:FORGE_DATABASE_FALLBACK_TO_LOCAL="false"
```

### Documentation

- **UI Dashboard:** <http://127.0.0.1:8000>
- **User Docs:** <http://127.0.0.1:8000/docs-site/user/>
- **Developer Docs:** <http://127.0.0.1:8000/docs-site/developer/>

Documentation source files are in `site_docs/` and are built with MkDocs Material.

## Admin Setup Guide (All Functionalities)

Use this checklist when provisioning a full environment for users, registration, password reset, and integrations.

1. Base environment

```powershell
Copy-Item .env.example .env
```

2. Core application settings

```powershell
$env:FORGE_ENV="dev"
$env:FORGE_JWT_SECRET="<strong-random-secret>"
$env:FORGE_PUBLIC_BASE_URL="http://127.0.0.1:8000"
```

3. Database settings

```powershell
# SQLite (simple local mode)
$env:FORGE_DATABASE_URL="sqlite:///./foundry.db"

# Optional local fallback behavior
$env:FORGE_DATABASE_FALLBACK_TO_LOCAL="true"
$env:FORGE_DATABASE_CONNECT_TIMEOUT_SECONDS="5"
```

4. Email settings (required for register + forgot-password)

```powershell
$env:FORGE_SMTP_HOST="smtp.office365.com"
$env:FORGE_SMTP_PORT="587"
$env:FORGE_SMTP_USERNAME="<smtp-user>"
$env:FORGE_SMTP_PASSWORD="<smtp-password-or-app-password>"
$env:FORGE_SMTP_FROM_EMAIL="noreply@your-domain.com"
$env:FORGE_SMTP_STARTTLS="true"
$env:FORGE_SMTP_USE_SSL="false"
```

5. Integration settings

```powershell
$env:FORGE_CELONIS_API_TOKEN="<celonis-token>"
$env:FORGE_GITLAB_BASE_URL="https://gitlab.com"
$env:FORGE_GITLAB_API_TOKEN="<gitlab-token>"
```

6. Start and validate

```powershell
uvicorn foundry.api.main:app --reload
```

- Check health: <http://127.0.0.1:8000/health>
- Check docs: <http://127.0.0.1:8000/docs>
- Open login: <http://127.0.0.1:8000/login>

7. Functional smoke test

- Register a new user at `/register` and verify email link delivery.
- Request password reset at `/forgot-password` and verify reset email delivery.
- Sign in and open `/account-ui` to update profile/password.
- Open `/dashboard` and verify Celonis and GitLab cards load with configured tokens.

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

Docker forces the API container to use the bundled Postgres service even if `.env` is configured for local SQLite.

## Startup Troubleshooting

- `psycopg.errors.ConnectionTimeout` during startup means your configured Postgres instance is unreachable.
- In local `dev`, the app now falls back to `FORGE_LOCAL_DATABASE_URL` when `FORGE_DATABASE_FALLBACK_TO_LOCAL=true`.
- If `FORGE_LOCAL_DATABASE_URL` is not set, fallback uses `%LOCALAPPDATA%/CelonisDeliveryForge/foundry-local.db`.
- The initial Postgres reachability probe now uses `FORGE_DATABASE_CONNECT_TIMEOUT_SECONDS` so fallback happens quickly instead of hanging for a long startup window.
- Check `/health` to confirm the active backend and startup mode.
- To require Postgres locally, disable fallback and point `FORGE_DATABASE_URL` at a reachable database.

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
- `POST /forum-insights/` create a forum-derived insight item
- `GET /forum-insights/` list forum insights with filters
- `PATCH /forum-insights/{insight_id}` update lifecycle, ownership, and priority
- `POST /celonis/connections/upsert` upsert tenant-scoped Celonis connection
- `GET /celonis/connections` list configured Celonis connections
- `GET /celonis/connections/{client_id}/preflight` run service-scoped connection diagnostics (`service`, optional `probe_path` override)
- `POST /celonis/connections/{client_id}/preflight/batch` run multi-service diagnostics in one call (optional comma-separated `services`)
- `GET /celonis/connections/{client_id}/preflight/history` read persisted preflight snapshots (`limit`)
- `POST /celonis/extract` trigger API extract call for a client connection
- `POST /celonis/import` trigger API import call for a client connection
- `POST /use-cases/` create use-case library entry
- `GET /use-cases/` list and search use cases with filters
- `PATCH /use-cases/{use_case_id}` update use case metadata and visibility flags
- `POST /use-cases/roadmap` create roadmap progress item
- `GET /use-cases/roadmap` list roadmap progress items
- `PATCH /use-cases/roadmap/{item_id}` update roadmap progress

## Companion Workflow

- Open `/dashboard` and use the Celonis cards:
	- **Celonis Connection**: bind a `client` to a `tenant base URL`.
	- **Celonis Preflight**: choose a Celonis service scope and run connectivity/permission diagnostics (optional custom probe path).
	- **Celonis Preflight (All Services)**: run one-click batch diagnostics and persist snapshot results for history/audit.
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

## Open-Source Integration Workflow

Use git submodules to vendor upstream open-source repos while keeping Forge customizations in first-party code.

Bootstrap a new upstream dependency:

```powershell
.\scripts\add_upstream_submodule.ps1 -UpstreamUrl "https://github.com/<owner>/<repo>.git" -Name "<alias>" -Branch "main"
```

The script creates:

- Submodule path under `vendor/<alias>`
- Metadata record in `.upstreams/<alias>.json`
- Patch queue directory at `patches/<alias>/`

Detailed guidance: `docs/open-source-submodule-workflow.md`

## Roadmaps

- Master roadmap: `docs/master-roadmap.md`
- Engineering roadmap: `docs/dev-roadmap.md`
- Agent and Celonis coverage roadmap: `docs/agent-feature-roadmap.md`
- Celonis support forum insights roadmap: `docs/celonis-forum-insights-roadmap.md`
- Agent orchestrators adoption roadmap: `docs/agent-orchestrators-roadmap.md`
- Agent orchestration operating model: `docs/agent-orchestration-operating-model.md`
- Consultant support agent pack: `docs/consultant-agent-pack.md`

## Agent Run Bootstrap

Create an isolated, governed agent run with one command:

```powershell
.\scripts\new_agent_run.ps1 -TaskId O6-PILOT-001 -Title "Parallel merge safety pilot" -Agent codex -Lane pilot -BaseBranch main
```

This creates a dedicated worktree in `.worktrees/` and a run card in `.orchestration/runs/`.

Move a run through governed closure states:

```powershell
.\scripts\close_agent_run.ps1 -RunCard .\.orchestration\runs\<run-id>.md -Status "IN REVIEW"
.\scripts\close_agent_run.ps1 -RunCard .\.orchestration\runs\<run-id>.md -Status "DONE"
```

The close script enforces evidence and review gates before allowing status transitions.

List run cards for standup or triage:

```powershell
.\scripts\list_agent_runs.ps1
.\scripts\list_agent_runs.ps1 -Summary
.\scripts\list_agent_runs.ps1 -Summary -Json
.\scripts\list_agent_runs.ps1 -Status "IN REVIEW"
.\scripts\list_agent_runs.ps1 -Detailed
```

Create consultant support runs with workflow presets:

```powershell
.\scripts\new_consultant_agent_run.ps1 -TaskId C-W13-001 -Preset Discovery -Owner "Delivery Forge core team" -Agent codex -BaseBranch main
```

Supported presets: `Discovery`, `WorkshopPrep`, `KPIDesign`, `IssueTriage`, `SteeringPack`, `RiskReview`, `ClientComms`, `FollowUp`.

## Celonis Asset Intelligence

- **Agent-readable feature coverage roadmap**: `docs/agent-feature-roadmap.md`

# Developers

Florian Berthold - 2026 - florian.d.berthold@gmail.com