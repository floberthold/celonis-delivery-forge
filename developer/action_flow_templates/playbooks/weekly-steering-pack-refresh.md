# Weekly Steering Pack Refresh

## Outcome
Automate steering pack preparation with fresh KPI and risk content.

## Source spec
- `../specs/weekly-steering-pack-refresh.json`

## Setup
1. Select deck template and report owner.
2. Configure weekly schedule and data cut-off.
3. Configure fallback todo destination.

## Validation
1. Trigger weekly run manually.
2. Verify deck instantiation output.
3. Verify owner notification.

## Fallback
- Dead-letter path: `todo.create_manual_pack_task`
- Manual pack generation runbook if template service is unavailable.
