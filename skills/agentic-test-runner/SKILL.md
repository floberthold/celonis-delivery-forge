---
name: agentic-test-runner
description: Run test suites (smoke, core, e2e) and manage test artifacts. Track test execution, results, and coverage metrics.
---

# Agentic Test Runner Skill

Use this skill when an agent needs to:

- Execute test suites at different levels (smoke, core, e2e).
- Record test run artifacts and results.
- Validate test coverage and failure patterns.
- Inspect test execution traces for debugging.

## Tool usage order

1. Run the desired test level:
   - Smoke: `python -m foundry.mcp.agentic_test_runner run --test-type smoke`
   - Core: `python -m foundry.mcp.agentic_test_runner run --test-type core`
   - E2E: `python -m foundry.mcp.agentic_test_runner run --test-type e2e`
2. Review results in `.orchestration/test-runs/latest_results.json`
3. Optionally export or dry-run: `--no-persist-results`

## Expected outputs

- Test execution summary (passed/failed/skipped counts).
- Detailed test run records with timestamps.
- Latest results JSON for automation integration.

## Safety rules

- Always run smoke tests before proceeding to core or e2e.
- Do not modify test files during execution.
- Preserve test artifacts for historical analysis.
- Report failure patterns explicitly when detected.
