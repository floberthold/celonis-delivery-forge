---
name: agentic-bug-ledger
description: Track bugs, failures, and regressions across test runs and deployments. Maintain comprehensive failure history and trend analysis.
---

# Agentic Bug Ledger Skill

Use this skill when an agent needs to:

- Record new bugs or failures discovered during testing.
- Query historical bug records and trends.
- Classify and prioritize failures by severity and component.
- Generate bug statistics and summary reports.
- Deduplicate related failure records.

## Tool usage order

1. Record a failure:
   - `python -m foundry.mcp.agentic_bug_ledger record --title "..." --severity <level> --component <name>`
2. List or analyze bugs:
   - `python -m foundry.mcp.agentic_bug_ledger list --limit <n>`
   - `python -m foundry.mcp.agentic_bug_ledger summary`
3. Export for reporting:
   - `python -m foundry.mcp.agentic_bug_ledger export --format json`

## Expected outputs

- Ledger event entries (appended to `.orchestration/bug-ledger/ledger.jsonl`).
- Aggregated statistics in `summary.json`.
- Severity and component classification.

## Safety rules

- Do not modify existing ledger entries; append only.
- Use consistent component names to enable trend analysis.
- Include clear reproduction steps or test case references.
- Mark critical/blocking bugs explicitly.
