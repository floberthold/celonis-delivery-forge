# agentic-evidence-retrieval skill

This skill provides standardized access to evidence artifacts for failing user journeys, including traces, screenshots, and logs.

## Quick start

```powershell
# Retrieve evidence for a failing journey
python -m foundry.mcp.agentic_evidence retrieve --journey-id "user-login-flow-202601" --scope full

# Get evidence summary only
python -m foundry.mcp.agentic_evidence retrieve --journey-id "user-login-flow-202601" --scope summary

# Export evidence package
python -m foundry.mcp.agentic_evidence export --journey-id "user-login-flow-202601" --format zip
```

## Artifacts

- `.orchestration/evidence/` - Evidence storage root
- `.orchestration/evidence/journeys/` - Journey recordings and traces
- `.orchestration/evidence/screenshots/` - Captured screenshots from failing tests
- `.orchestration/evidence/logs/` - Application and browser logs

## Evidence Types

- **Traces**: Full user journey execution traces
- **Screenshots**: Visual state at key decision points
- **Logs**: Browser console, server logs, test output
- **Metadata**: Timestamps, environment info, reproducer steps
