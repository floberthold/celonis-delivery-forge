# Configuration Reference

This is the operational reference for `FORGE_*` environment variables.

## Core App

| Variable | Default | Required | Notes |
| --- | --- | --- | --- |
| `FORGE_APP_NAME` | `Celonis Delivery Forge` | No | Display name and health payload |
| `FORGE_ENV` | `dev` | Yes | `dev`/`local` allow DB fallback |
| `FORGE_PUBLIC_BASE_URL` | empty | Yes for email flows | Used in verification/reset links |

## Database

| Variable | Default | Required | Notes |
| --- | --- | --- | --- |
| `FORGE_DATABASE_URL` | `sqlite:///./foundry.db` | Yes | Primary DB target |
| `FORGE_LOCAL_DATABASE_URL` | LocalAppData sqlite path | No | Fallback DB location |
| `FORGE_DATABASE_FALLBACK_TO_LOCAL` | `true` | No | Should be `false` in strict environments |
| `FORGE_DATABASE_CONNECT_TIMEOUT_SECONDS` | `5` | No | Connect timeout for non-sqlite backends |

## Authentication and Security

| Variable | Default | Required | Notes |
| --- | --- | --- | --- |
| `FORGE_JWT_SECRET` | `change-me` | Yes | Must be replaced for any real environment |
| `FORGE_JWT_ALGORITHM` | `HS256` | No | Keep default unless code changes |
| `FORGE_JWT_EXPIRE_MINUTES` | `720` | No | Session lifetime |
| `FORGE_REGISTRATION_TOKEN_EXPIRE_MINUTES` | `60` | No | Verification token expiry |
| `FORGE_PASSWORD_RESET_TOKEN_EXPIRE_MINUTES` | `30` | No | Reset token expiry |

## SMTP and Email

| Variable | Default | Required | Notes |
| --- | --- | --- | --- |
| `FORGE_SMTP_HOST` | empty | Yes for email | SMTP server hostname |
| `FORGE_SMTP_PORT` | `587` | Yes for email | Common: 587 STARTTLS, 465 SSL |
| `FORGE_SMTP_USERNAME` | empty | Yes for email | SMTP auth principal |
| `FORGE_SMTP_PASSWORD` | empty | Yes for email | Prefer app passwords |
| `FORGE_SMTP_FROM_EMAIL` | empty | Yes for email | Must be authorized sender |
| `FORGE_SMTP_STARTTLS` | `true` | No | Use with port 587 |
| `FORGE_SMTP_USE_SSL` | `false` | No | Use with port 465 |

## Integrations

| Variable | Default | Required | Notes |
| --- | --- | --- | --- |
| `FORGE_CELONIS_API_TOKEN` | empty | For Celonis features | System fallback token; per-user token saved in `/onboarding/celonis-setup` step 3 takes precedence |
| `FORGE_CELONIS_TIMEOUT_SECONDS` | `20` | No | Request timeout |
| `FORGE_GITLAB_BASE_URL` | empty | For GitLab features | Example: `https://gitlab.com` |
| `FORGE_GITLAB_API_TOKEN` | empty | For GitLab features | Needs sufficient API scope |

## Files and Uploads

| Variable | Default | Required | Notes |
| --- | --- | --- | --- |
| `FORGE_UPLOADS_DIR` | `./uploads` | No | Runtime upload storage |
| `FORGE_DELIVERY_FILE_MAX_UPLOAD_BYTES` | `26214400` | No | 25 MB default |
| `FORGE_CELONIS_SHARED_DIR` | `./Code from Celonis` | No | Local source directory for ingestion workflows |

## Safe Baseline (Local)

```powershell
$env:FORGE_ENV="dev"
$env:FORGE_JWT_SECRET="<strong-random-secret>"
$env:FORGE_PUBLIC_BASE_URL="http://127.0.0.1:8000"
$env:FORGE_DATABASE_URL="sqlite:///./foundry.db"
$env:FORGE_DATABASE_FALLBACK_TO_LOCAL="true"
$env:FORGE_DATABASE_CONNECT_TIMEOUT_SECONDS="5"
```
