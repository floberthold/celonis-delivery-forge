# Admin Full Setup

Use this runbook to configure all core functionalities including account verification and password reset.

## 1. Core Environment

```powershell
Copy-Item .env.example .env
$env:FORGE_ENV="dev"
$env:FORGE_JWT_SECRET="<strong-random-secret>"
$env:FORGE_PUBLIC_BASE_URL="http://127.0.0.1:8000"
```

## 2. Database

```powershell
$env:FORGE_DATABASE_URL="sqlite:///./foundry.db"
$env:FORGE_DATABASE_FALLBACK_TO_LOCAL="true"
$env:FORGE_DATABASE_CONNECT_TIMEOUT_SECONDS="5"
```

## 3. SMTP (Required for Register + Forgot Password)

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

- Microsoft 365: `smtp.office365.com`, port `587`, StartTLS `true`
- Gmail: `smtp.gmail.com`, port `587`, StartTLS `true` (use app password)

## 4. Integrations

```powershell
$env:FORGE_CELONIS_API_TOKEN="<celonis-token>"
$env:FORGE_GITLAB_BASE_URL="https://gitlab.com"
$env:FORGE_GITLAB_API_TOKEN="<gitlab-token>"
```

## 5. Start and Validate

```powershell
uvicorn foundry.api.main:app --reload
```

Validate:

1. Open `/health` and check backend/startup mode.
2. Open `/dashboard` and verify cards load.
3. Run registration flow at `/register`.
4. Run password reset flow at `/forgot-password`.
5. Confirm account updates in `/account-ui`.
