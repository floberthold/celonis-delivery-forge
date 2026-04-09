# Integrations

## Celonis

- Configure token with `FORGE_CELONIS_API_TOKEN`.
- Use dashboard cards to set client connection, run preflight, extract, and import.

## GitLab

- Configure `FORGE_GITLAB_BASE_URL` and `FORGE_GITLAB_API_TOKEN`.
- Validate repo connectivity and workflow behavior in related UI routes.

## Ingest and Snapshot Boundaries

- Treat ingest/snapshot actions as side-effecting boundaries.
- Validate organization scoping and permission checks on every route change.
