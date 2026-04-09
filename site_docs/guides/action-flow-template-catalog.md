# Action-Flow Template Catalog

The starter catalog is stored in `developer/action_flow_templates/` and includes 12 templates.

## Alerts and Escalation

- `kpi-threshold-alert-to-task-and-notify`
- `process-anomaly-escalation-chain`
- `data-quality-breach-stopline`

## Sync and Propagation

- `nightly-km-recommendation-sync`
- `subscription-event-materialized-sync`
- `weekly-steering-pack-refresh`

## Recommendation and Human Loop

- `recommendation-human-approval-gate`
- `priority-case-auto-routing`
- `closed-loop-action-effectiveness-feedback`

## AI-Assisted Triage

- `low-confidence-ai-triage-review-loop`
- `subscription-event-client-comms-draft`
- `stale-incomplete-execution-watchdog`

## How to Use

1. Pick a template from `specs/`.
2. Open its paired playbook from `playbooks/`.
3. Configure required inputs and routing.
4. Validate with sandbox payload.
5. Promote only after reviewer sign-off.
