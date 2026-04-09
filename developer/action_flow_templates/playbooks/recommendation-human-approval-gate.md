# Recommendation Human Approval Gate

## Outcome
Require explicit human approval before high-impact actions.

## Source spec
- `../specs/recommendation-human-approval-gate.json`

## Setup
1. Define approval role and timeout.
2. Define approval packet content.
3. Enable stale-approval escalation.

## Validation
1. Trigger one high-impact recommendation event.
2. Confirm approval task creation.
3. Confirm approved and rejected branches both work.

## Fallback
- Dead-letter path: `notify.approval_stale`
- Auto-close unresolved items with manual follow-up task.
