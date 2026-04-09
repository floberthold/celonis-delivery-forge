# Quick Start

This page gets a new environment running quickly with working login, docs, and core UI.

## Prerequisites

- Python 3.11+
- A virtual environment (recommended)
- Project checked out locally

## 1. Configure Environment

```powershell
Copy-Item .env.example .env
```

Set minimum required variables:

```powershell
$env:FORGE_ENV="dev"
$env:FORGE_JWT_SECRET="<strong-random-secret>"
$env:FORGE_PUBLIC_BASE_URL="http://127.0.0.1:8000"
```

## 2. Install Dependencies

```powershell
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

## 3. Start the App

```powershell
uvicorn foundry.api.main:app --reload
```

## 4. Verify Runtime Health

Open:

- `http://127.0.0.1:8000/health`
- `http://127.0.0.1:8000/docs`
- `http://127.0.0.1:8000/dashboard`
- `http://127.0.0.1:8000/docs-site/`

Expected `/health` response includes:

- `status: ok`
- `database_backend`: `sqlite` or `postgresql`
- `database_startup_mode`: `configured` or `local_fallback`

## 5. Create and Verify a User

1. Open `/register`.
2. Complete registration.
3. Confirm email verification if SMTP is configured.
4. Sign in at `/login`.
5. Open `/account-ui`.

## 6. Run Essential Tests

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_login_ui.py tests/test_account_ui.py -q
```

## Common Startup Issues

- `Configured database is unavailable`: app may use local fallback if enabled.
- Redirect loop to `/login`: account may miss organization membership or token expired.
- No verification email: SMTP settings are missing or invalid.

See troubleshooting pages for deeper diagnosis.
