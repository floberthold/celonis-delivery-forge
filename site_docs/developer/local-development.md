# Local Development

This page provides the default workflow for contributors.

## Setup

```powershell
Copy-Item .env.example .env
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

## Run API

```powershell
uvicorn foundry.api.main:app --reload
```

Useful URLs:

- `http://127.0.0.1:8000/docs`
- `http://127.0.0.1:8000/health`
- `http://127.0.0.1:8000/dashboard`
- `http://127.0.0.1:8000/docs-site/`

## Preferred Local Test Commands

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_login_ui.py tests/test_account_ui.py -q
.\.venv\Scripts\python.exe -m pytest tests/test_celonis_preflight_api.py -q
.\.venv\Scripts\python.exe -m pytest tests/test_docs_site_routes.py -q
```

## Development Conventions

- Add route changes with matching tests.
- Preserve organization scoping checks for all entity operations.
- Keep UI and API auth behavior aligned.
- Update documentation pages when user-visible behavior changes.
