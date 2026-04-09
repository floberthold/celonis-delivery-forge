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

## Action-Flow Template Contract

Use the action-flow template library in `developer/action_flow_templates/` as the
canonical spec source for reusable automation flows.

Required contract components:

- `schema/action-flow-template.schema.json` defines required structure.
- `specs/*.json` define executable flow logic and safety policies.
- `playbooks/*.md` define consultant rollout and validation guidance.

Integration guidance:

- Map template inputs to `Template.prefill_schema_json` when exposing templates in UI.
- Persist flow metadata and schema version in `AssetSnapshot.summary_json`.
- Register published flows as assets with `Asset.type = action_flow`.
- Enforce evidence and reviewer gates for medium/high risk templates.

Operational defaults:

- Make dead-letter behavior explicit for every template.
- Keep max retries bounded and documented per template.
- Use sequential processing for high-risk or approval-gated templates.

## SMTP and Email Actions

- Registration and reset flows rely on SMTP runtime configuration.
- For local testing, mock or patch email sending where possible.
- Ensure token link generation uses `FORGE_PUBLIC_BASE_URL`.
