# Celonis Extraction Readiness Checklist

Date: 2026-05-10
Scope: Phase 2 preconditions before splitting Celonis domain into a dedicated submodule/repository.

## Objective

Ensure the Celonis boundary is contract-stable, operationally observable, and regression-safe before extraction.

## Gate Checklist

### 1) Contract Stability

- [ ] Shared API contracts in use for Celonis route errors.
- [ ] MCP invocation/response DTO contracts documented and applied.
- [ ] Explicit error-code taxonomy documented for Celonis flows.

Current evidence:

- `src/foundry/contracts.py`
- `src/foundry/api/routes/celonis.py`
- `tests/test_shared_api_contracts.py`
- `tests/test_celonis_data_agent_contracts.py`

### 2) Adapter Boundary Behavior

- [ ] Timeout behavior classified and test-covered.
- [ ] Rate-limit behavior classified and test-covered.
- [ ] Upstream 5xx behavior classified and test-covered.
- [ ] Fallback endpoint behavior test-covered.

Current evidence:

- `src/foundry/services/celonis_data_agent_service.py`
- `tests/test_celonis_data_agent_contracts.py`

### 3) Deployment Governance

- [ ] Write tools are approval-bound.
- [ ] Deployment request validation is enforced.
- [ ] Client/package mismatch is rejected.

Current evidence:

- `src/foundry/api/routes/celonis.py`
- `tests/test_celonis_user_token_api.py`

### 4) Rollout and Profile Safety

- [ ] Domain gating for Celonis UI is enforced.
- [ ] Tool-hub profile filtering is active.
- [ ] Profile regression pack includes integration-celonis and full profiles.

Current evidence:

- `tests/test_ui_domain_profile_gating.py`
- `tests/test_tool_hub_profile_activation.py`
- `scripts/run_profile_regression_pack.ps1`

### 5) Operational Runbook Readiness

- [ ] Extraction cutover runbook drafted.
- [ ] Rollback strategy documented.
- [ ] Ownership and release policy documented.

## Verification Commands

```powershell
pytest tests/test_celonis_data_agent_contracts.py tests/test_celonis_user_token_api.py tests/test_tool_hub_profile_activation.py tests/test_ui_domain_profile_gating.py
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\run_profile_regression_pack.ps1 -Profiles integration-celonis,full -SkipDependencyInstall
```

## Exit Criteria

Extraction can proceed when all checklist items are complete and the latest regression-pack artifact for `integration-celonis` and `full` profiles is green.
