# Testing Strategy

This page describes practical test layers and commonly used commands.

## Test Layers

- API behavior tests.
- UI route/template behavior tests.
- Startup and database policy tests.
- Integration-adjacent tests (Celonis/GitLab behavior where feasible).
- Documentation route/redirect tests.

## Frequently Used Test Commands

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_login_ui.py tests/test_account_ui.py -q
.\.venv\Scripts\python.exe -m pytest tests/test_people_ui.py -q
.\.venv\Scripts\python.exe -m pytest tests/test_celonis_preflight_api.py -q
.\.venv\Scripts\python.exe -m pytest tests/test_celonis_marketplace_api.py -q
.\.venv\Scripts\python.exe -m pytest tests/test_docs_site_routes.py -q
```

## Regression Expectations

When changing auth, routing, or account flows:

- Run login/account UI tests.
- Run affected route tests.
- Validate docs route tests if doc URLs or redirects changed.

When changing DB startup logic:

- Run startup policy tests.
- Validate `/health` semantics remain stable.

## Documentation Validation

```powershell
.\.venv\Scripts\python.exe -m mkdocs build --strict
```

Any strict build warning should be treated as a release blocker for docs updates.
