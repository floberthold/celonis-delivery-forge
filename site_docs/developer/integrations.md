# Integrations

## Celonis

- Configure `FORGE_CELONIS_API_TOKEN` and tenant connection details.
- Use dashboard actions to run connect/preflight/extract/import flows.
- Validate behavior using API tests before release.

Recommended validation path:

1. Configure token.
2. Save connection from dashboard.
3. Run single-service preflight.
4. Run batch preflight.
5. Confirm expected statuses and persisted history.

## GitLab

- Configure `FORGE_GITLAB_BASE_URL` and `FORGE_GITLAB_API_TOKEN`.
- Validate repository connectivity and token scope.
- Verify route behavior for expected project/repo operations.

## Ingest and Snapshot Boundaries

- Treat ingest/snapshot actions as side-effecting boundaries.
- Validate organization scoping and permission checks on every route change.

## SMTP and Email Actions

- Registration and reset flows rely on SMTP runtime configuration.
- For local testing, mock or patch email sending where possible.
- Ensure token link generation uses `FORGE_PUBLIC_BASE_URL`.
