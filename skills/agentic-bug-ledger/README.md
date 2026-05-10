# agentic-bug-ledger skill

This skill provides a standardized interface for tracking bugs, failures, and regressions across test runs and deployments.

## Quick start

```powershell
# Record a new bug/failure
python -m foundry.mcp.agentic_bug_ledger record --title "Login fails on Safari" --severity critical --component auth

# List recent bugs
python -m foundry.mcp.agentic_bug_ledger list --limit 20

# Get summary statistics
python -m foundry.mcp.agentic_bug_ledger summary

# Export ledger for reporting
python -m foundry.mcp.agentic_bug_ledger export --format json
```

## Artifacts

- `.orchestration/bug-ledger/` - Ledger records directory
- `.orchestration/bug-ledger/ledger.jsonl` - Append-only event log
- `.orchestration/bug-ledger/summary.json` - Aggregated statistics

## Features

- Automatic severity inference
- Component/subsystem classification
- Relation to test runs via trace IDs
- De-duplication detection
- Historical trend analysis
