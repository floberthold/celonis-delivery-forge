# Admin Full Setup

Use this runbook to provision an environment that supports all major features: account lifecycle, governed delivery workflows, and integrations.

## Phase 1: Baseline Environment

```powershell
Copy-Item .env.example .env
$env:FORGE_ENV="dev"
$env:FORGE_JWT_SECRET="<strong-random-secret>"
$env:FORGE_PUBLIC_BASE_URL="http://127.0.0.1:8000"
```

## Phase 2: Database Configuration

```powershell
$env:FORGE_DATABASE_URL="sqlite:///./foundry.db"
$env:FORGE_DATABASE_FALLBACK_TO_LOCAL="true"
$env:FORGE_DATABASE_CONNECT_TIMEOUT_SECONDS="5"
```

Guidance:

- In strict environments, set `FORGE_DATABASE_FALLBACK_TO_LOCAL=false`.
- Keep one canonical DB target per environment to avoid split-state confusion.

## Phase 3: SMTP for Registration and Password Reset

```powershell
$env:FORGE_SMTP_HOST="smtp.office365.com"
$env:FORGE_SMTP_PORT="587"
$env:FORGE_SMTP_USERNAME="<smtp-user>"
$env:FORGE_SMTP_PASSWORD="<smtp-password-or-app-password>"
$env:FORGE_SMTP_FROM_EMAIL="noreply@your-domain.com"
$env:FORGE_SMTP_STARTTLS="true"
$env:FORGE_SMTP_USE_SSL="false"
```

Provider defaults:

- Microsoft 365: `smtp.office365.com`, port `587`, STARTTLS.
- Gmail: `smtp.gmail.com`, port `587`, app password required.

## Phase 4: Integration Variables

```powershell
$env:FORGE_CELONIS_API_TOKEN="<celonis-token>"
$env:FORGE_GITLAB_BASE_URL="https://gitlab.com"
$env:FORGE_GITLAB_API_TOKEN="<gitlab-token>"
```

## Phase 5: Start Runtime

```powershell
uvicorn foundry.api.main:app --reload
```

## Phase 6: Admin Validation Sequence

1. Open `/health` and verify backend/startup mode.
2. Open `/login` and `/register`.
3. Complete one register + verify + login flow.
4. Open `/account-ui` and test profile update.
5. Open `/dashboard` and run at least one Celonis preflight.
6. Open `/people-ui`, `/projects-ui`, `/reviews-ui`, and `/timeline-ui`.

## Exit Criteria

- Authentication lifecycle works end-to-end.
- Core workspaces are reachable and persistent.
- Integrations are configured and validated.
- Admin can provision and manage users.
