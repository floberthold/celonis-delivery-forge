# KPI Threshold Alert to Task and Notify

## Outcome
Trigger fast containment when KPI values exceed a threshold.

## Source spec
- `../specs/kpi-threshold-alert-to-task-and-notify.json`

## Setup
1. Set KPI source and threshold.
2. Configure owner and escalation channel.
3. Enable sequential processing for deterministic ordering.

## Validation
1. Run dry payload with known breach.
2. Confirm one task created.
3. Confirm notification event in timeline.

## Fallback
- Dead-letter path: `timeline.log_and_escalate`
- Manual owner override if routing fails.
