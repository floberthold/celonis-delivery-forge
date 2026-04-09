# Process Anomaly Escalation Chain

## Outcome
Escalate high-risk anomalies through a controlled chain.

## Source spec
- `../specs/process-anomaly-escalation-chain.json`

## Setup
1. Set anomaly score threshold.
2. Configure role routing and management escalation contacts.
3. Set SLA timer and fallback queue.

## Validation
1. Replay one critical anomaly event.
2. Verify incident task creation.
3. Verify primary and management notifications.

## Fallback
- Dead-letter path: `risk_queue.create_case`
- Commit partial state and continue management visibility.
