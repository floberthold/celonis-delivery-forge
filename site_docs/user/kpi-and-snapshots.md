# KPI and Snapshot Operations

Use these pages for KPI lifecycle management and evidence collection.

## KPI Editor (`/kpis-ui`)

Use to create and maintain KPI definitions.

Typical actions:

- Create KPI with formula and metadata.
- Update versions as formulas evolve.
- Review status progression over time.

## KPI Book (`/kpi-book-ui/{client_id}`)

Use to maintain client-scoped KPI snapshots and curated KPI references.

Typical actions:

- Review KPI entries bound to a client.
- Compare KPI state with snapshot outputs.
- Prepare KPI handover artifacts.

## Snapshots (`/snapshots-ui/{client_id}`)

Use to capture platform snapshots and inspect content detail.

Typical actions:

- Trigger new snapshot runs.
- Inspect snapshot status and metadata.
- Open detail page for package/model/job breakdown.

## Recommended Workflow

1. Ensure Celonis connectivity from dashboard preflight.
2. Run a snapshot for the target client.
3. Open snapshot detail and validate expected artifacts.
4. Update KPI definitions in `/kpis-ui` where needed.
5. Curate final KPI set in KPI Book.

## Validation Checklist

- Snapshot appears in client snapshot list.
- Snapshot detail opens without errors.
- KPI updates are persisted and visible on refresh.
- KPI Book reflects intended client-specific output.
