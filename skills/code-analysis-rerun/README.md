# code-analysis-rerun skill

This skill standardizes how agents rerun repository analysis and refresh report metrics.

## Quick start

```powershell
python -m foundry.mcp.agentic_code_analysis run
```

## Artifacts

- `.orchestration/code-analysis/latest_metrics.json`
- `.orchestration/code-analysis/next-improvements-prompt.md`

## Dry run without changing reports

```powershell
python -m foundry.mcp.agentic_code_analysis run --no-update-reports
```
