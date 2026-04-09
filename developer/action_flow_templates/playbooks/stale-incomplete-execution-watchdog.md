# Stale Incomplete Execution Watchdog

## Outcome
Detect and triage incomplete runs before they become operational incidents.

## Source spec
- `../specs/stale-incomplete-execution-watchdog.json`

## Setup
1. Set stale-time threshold.
2. Configure triage owner and operations channel.
3. Configure incident escalation for repeated stale runs.

## Validation
1. Seed stale run entries in test queue.
2. Confirm triage tasks are opened.
3. Confirm operations channel notification is sent.

## Fallback
- Dead-letter path: `incident.raise`
- Manual run recovery playbook for critical workflows.
