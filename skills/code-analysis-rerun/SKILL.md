---
name: code-analysis-rerun
description: Re-run full and active codebase analysis, refresh report metrics in existing docs, and produce an LLM-ready next-improvements brief.
---

# Code Analysis Rerun Skill

Use this skill when an agent needs to:

- Recompute repo metrics after refactors.
- Refresh existing report files without changing their structure.
- Produce a prompt that asks another LLM for prioritized next improvements.

## Tool usage order

1. Run the MCP-style CLI tool:
   - `python -m foundry.mcp.agentic_code_analysis run`
2. Read generated artifacts:
   - `.orchestration/code-analysis/latest_metrics.json`
   - `.orchestration/code-analysis/next-improvements-prompt.md`
3. If needed, run without modifying reports:
   - `python -m foundry.mcp.agentic_code_analysis run --no-update-reports`

## Expected outputs

- Updated report files (metrics/current-state values only).
- Machine-readable metrics JSON for automation.
- LLM prompt markdown for “what to improve next”.

## Safety rules

- Do not restructure report files; only update metrics/state values.
- Preserve existing report section ordering and headings.
- If path/number mismatches are detected, report them explicitly in output.
