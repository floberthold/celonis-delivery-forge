# agentic-test-runner skill

This skill standardizes how agents run test suites and manage test artifacts across the repository.

## Quick start

```powershell
# Run smoke tests
python -m foundry.mcp.agentic_test_runner run --test-type smoke

# Run core tests
python -m foundry.mcp.agentic_test_runner run --test-type core

# Run e2e tests
python -m foundry.mcp.agentic_test_runner run --test-type e2e

# Run specific test file
python -m foundry.mcp.agentic_test_runner run tests/test_methodology_ui.py
```

## Artifacts

- `.orchestration/test-runs/` - Test run records with timestamps
- `.orchestration/test-runs/latest_results.json` - Most recent test run summary

## Test Types

- **smoke**: Quick validation tests (`test_methodology_ui.py`, `test_celonis_ui_route_presence.py`)
- **core**: Foundation tests including smoke + integration tests
- **e2e**: End-to-end Playwright browser tests

## Dry run without persisting results

```powershell
python -m foundry.mcp.agentic_test_runner run --no-persist-results
```
