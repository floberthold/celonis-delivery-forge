# Replatform Implementation Tracker

Date baseline: 2026-05-10
Scope: Integrated from analysis and roadmap documents listed in `docs/domain-submodule-local-first-replatform.md`.

## Rules

- Every completed task must update:
  - This tracker
  - `docs/code-quality-and-cleanup-roadmap.md`
  - The task-specific implementation document
- Every completion entry should include test evidence and artifact path when available.

## Task List (Execution Order)

### 1) Phase 1 Contract Standardization

- [x] Create shared API contract schemas for error/health DTOs.
- [ ] Define and centralize error classification constants.
- [x] Add multi-tenancy context contract type.
- [x] Add MCP invocation/response DTO contract.
- [ ] Publish contract usage guide in developer docs.

Evidence:

- `src/foundry/contracts.py`
- `tests/test_shared_api_contracts.py`
- `src/foundry/api/routes/celonis.py` (error helper now uses shared contract model)

Documentation updates required:

- `docs/code-quality-and-cleanup-roadmap.md`
- `docs/code-analysis-complete-guide.md`

### 2) Phase 1 Tool Hub + Rollout Hardening

- [x] Activation-phase profile filtering in startup/catalog.
- [x] Profile/domain UI route gating for Celonis and Knowledge views.
- [x] Profile regression pack automation and artifact generation.
- [x] Add profile-aware health summary to status output.
- [x] Add profile-specific seed data support.

Evidence:

- `scripts/run_profile_regression_pack.ps1`
- `./.orchestration/test-runs/profile-regression/regression-pack-20260510T141345Z.json`
- `agentic/tool-hub/start_tool_hub.ps1`
- `tests/test_tool_hub_startup_catalog.py`
- `config/profile_seed_plan.json`
- `scripts/seed_profile_data.ps1`
- `tests/test_profile_seed_data_strategy.py`

Documentation updates required:

- `docs/code-quality-and-cleanup-roadmap.md`
- `docs/domain-submodule-local-first-replatform.md`

### 3) Phase 1 Celonis Boundary Hardening

- [x] Celonis data-agent contract tests (fallback and endpoint failure behavior).
- [x] Structured invoke-route errors (`error_code`, `request_id`).
- [x] Adapter timeout/rate-limit/upstream error semantics.
- [ ] Standardized health probe response semantics across domains.

Evidence:

- `tests/test_celonis_data_agent_contracts.py`
- `tests/test_celonis_user_token_api.py`

Documentation updates required:

- `docs/code-quality-and-cleanup-roadmap.md`
- `docs/codebase-metrics-and-analysis.md`

### 4) Phase 1a UI Route Decomposition

- [ ] Create `src/foundry/api/routes/ui/` package skeleton.
- [ ] Extract shared helper layer from `ui.py`.
- [x] Move first extracted route to dedicated module (`/local-knowledge-ui/status`) + tests.
- [ ] Move `navigation` routes + tests.
- [ ] Move `integrations` routes + tests.
- [ ] Move `admin/templates/health` routes + tests.
- [ ] Keep backward-compatible imports until full cutover.

Evidence:

- `src/foundry/api/routes/ui_knowledge_status.py`
- `src/foundry/api/main.py`
- `src/foundry/api/routes/ui.py`
- `tests/test_local_knowledge_ui.py`

Documentation updates required:

- `docs/refactoring-ui-routes.md`
- `docs/code-quality-and-cleanup-roadmap.md`

### 5) Phase 1b Service Domain Restructuring

- [x] Publish service-to-domain mapping table.
- [ ] Create package scaffolding (`platform`, `delivery`, `celonis`, `knowledge`, `integrations`, `orchestration`, `shared`).
- [ ] Migrate low-risk services and keep shims.
- [ ] Migrate high-coupling services and remove shims.
- [ ] Confirm import stability with test suite.

Evidence:

- `config/service_domain_mapping.json`
- `docs/service-domain-mapping.md`
- `tests/test_service_domain_mapping.py`

Documentation updates required:

- `docs/service-layer-restructuring.md`
- `docs/code-quality-and-cleanup-roadmap.md`

### 6) Phase 2 Extraction Readiness

- [x] Define extraction boundary checklist for Celonis split.
- [ ] Confirm all boundary tests green in full regression pack.
- [ ] Publish extraction runbook draft.

Evidence:

- `docs/celonis-extraction-readiness-checklist.md`

Documentation updates required:

- `docs/code-quality-and-cleanup-roadmap.md`
- `docs/domain-submodule-local-first-replatform.md`

## Latest Verification

- Targeted suites (Celonis + contracts): passing
- Multi-profile regression pack: passing
- Last known full artifact:
  - `./.orchestration/test-runs/profile-regression/regression-pack-20260510T140245Z.json`
