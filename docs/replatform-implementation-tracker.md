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
- [x] Define and centralize error classification constants.
- [x] Add multi-tenancy context contract type.
- [x] Add MCP invocation/response DTO contract.
- [x] Publish contract usage guide in developer docs.

Evidence:

- `src/foundry/contracts.py`
- `src/foundry/error_codes.py`
- `tests/test_shared_api_contracts.py`
- `src/foundry/api/routes/celonis.py` (error helper now uses shared contract model)
- `site_docs/developer/api-contracts.md`

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
- [x] Standardized health probe response semantics across domains.

Evidence:

- `tests/test_celonis_data_agent_contracts.py`
- `tests/test_celonis_user_token_api.py`
- `src/foundry/api/main.py`
- `src/foundry/api/routes/local_knowledge.py`
- `tests/test_startup_db_policy.py`
- `tests/test_local_knowledge_health_contracts.py`

Documentation updates required:

- `docs/code-quality-and-cleanup-roadmap.md`
- `docs/codebase-metrics-and-analysis.md`

### 4) Phase 1a UI Route Decomposition

- [x] Create `src/foundry/api/routes/ui/` package skeleton.
- [x] Extract shared helper layer from `ui.py`.
- [x] Move first extracted route to dedicated module (`/local-knowledge-ui/status`) + tests.
- [x] Move `navigation` routes + tests.
- [x] Move first `integrations` route slices (`/methodology-ui`, `/celonis-tool-hub-ui`) + tests.
- [x] Move `admin/templates/health` routes + tests.
- [x] Keep backward-compatible imports until full cutover.

Progress note:

- `templates` route slice extracted (`/templates-ui`) with dedicated coverage.
- `admin`-adjacent documentation redirect routes extracted (`/docu/*.html`) with dedicated coverage.

Evidence:

- `src/foundry/api/routes/ui_knowledge_status.py`
- `src/foundry/api/main.py`
- `src/foundry/api/routes/ui/__init__.py`
- `src/foundry/api/routes/ui/shared.py`
- `src/foundry/api/routes/ui/navigation.py`
- `src/foundry/api/routes/ui/integrations.py`
- `src/foundry/api/routes/ui/template_management.py`
- `src/foundry/api/routes/ui/docu_redirects.py`
- `src/foundry/api/routes/ui/admin_management.py`
- `src/foundry/api/routes/ui/celonis_setup_wizard.py`
- `src/foundry/api/routes/ui/client_health.py`
- `tests/test_local_knowledge_ui.py`
- `tests/test_ui_navigation_routes.py`
- `tests/test_ui_integrations_routes.py`
- `tests/test_celonis_tool_hub_ui.py`
- `tests/test_ui_templates_routes.py`
- `tests/test_ui_docu_redirect_routes.py`
- `tests/test_foundry_admin_ui.py`
- `tests/test_tenant_setup_wizard_ui.py`
- `tests/test_client_health_ui.py`

Documentation updates required:

- `docs/refactoring-ui-routes.md`
- `docs/code-quality-and-cleanup-roadmap.md`

### 5) Phase 1b Service Domain Restructuring

- [x] Publish service-to-domain mapping table.
- [x] Create package scaffolding (`platform`, `delivery`, `celonis`, `knowledge`, `integrations`, `orchestration`, `shared`).
- [x] Migrate low-risk services and keep shims.
- [x] Migrate high-coupling services and remove shims.
- [x] Confirm import stability with test suite.

Evidence:

- `config/service_domain_mapping.json`
- `docs/service-domain-mapping.md`
- `tests/test_service_domain_mapping.py`
- `src/foundry/services/platform/__init__.py`
- `src/foundry/services/delivery/__init__.py`
- `src/foundry/services/celonis/__init__.py`
- `src/foundry/services/knowledge/__init__.py`
- `src/foundry/services/integrations/__init__.py`
- `src/foundry/services/orchestration/__init__.py`
- `src/foundry/services/shared/__init__.py`
- `tests/test_service_domain_package_scaffolding.py`
- `src/foundry/services/platform/feature_rollout.py`
- `src/foundry/services/integrations/email_service.py`
- `src/foundry/services/delivery/template_seed.py`
- `src/foundry/services/knowledge/use_case_views.py`
- `src/foundry/services/integrations/trycelonis_demo_rebuild.py`
- `src/foundry/services/integrations/ingest_service.py`
- `src/foundry/services/delivery/florian_script_seed.py`
- `src/foundry/services/feature_rollout.py` (compat shim)
- `src/foundry/services/email_service.py` (compat shim)
- `src/foundry/services/template_seed.py` (compat shim)
- `src/foundry/services/use_case_views.py` (compat shim)
- `src/foundry/services/trycelonis_demo_rebuild.py` (compat shim)
- `src/foundry/services/ingest_service.py` (compat shim)
- `src/foundry/services/florian_script_seed.py` (compat shim)
- `src/foundry/services/delivery/activity_log.py`
- `src/foundry/services/delivery/project_service.py`
- `src/foundry/services/delivery/review_service.py`
- `src/foundry/services/delivery/template_service.py`
- `src/foundry/services/delivery/todo_service.py`
- `src/foundry/services/activity_log.py` (compat shim)
- `src/foundry/services/project_service.py` (compat shim)
- `src/foundry/services/review_service.py` (compat shim)
- `src/foundry/services/template_service.py` (compat shim)
- `src/foundry/services/todo_service.py` (compat shim)
- `src/foundry/services/celonis/celonis_contracts.py`
- `src/foundry/services/celonis/celonis_data_agent_service.py`
- `src/foundry/services/celonis/celonis_deployment_service.py`
- `src/foundry/services/celonis/celonis_payload_extractors.py`
- `src/foundry/services/celonis/snapshot_service.py`
- `src/foundry/services/celonis/snapshot_coverage_service.py`
- `src/foundry/services/celonis/snapshot_detail_extractors.py`
- `src/foundry/services/celonis/snapshot_export_service.py`
- `src/foundry/services/celonis/snapshot_git_service.py`
- `src/foundry/api/routes/celonis.py`
- `src/foundry/api/routes/celonis_deployments.py`
- `src/foundry/api/routes/snapshots.py`
- `src/foundry/api/routes/ingest.py`
- `src/foundry/api/routes/ui/integrations.py`
- `tests/test_service_low_risk_shims.py`
- `tests/test_ingest_repo_sync_api.py`
- `tests/test_foundry_admin_ui.py`
- `tests/test_tenant_setup_wizard_ui.py`
- `tests/test_client_health_ui.py`
- `tests/test_ui_templates_routes.py`
- `tests/test_celonis_ui_route_presence.py`
- `tests/test_celonis_data_agent_contracts.py`
- `tests/test_snapshot_detail_extraction.py`
- `tests/test_snapshots_api.py`
- `tests/test_service_domain_mapping.py`

Documentation updates required:

- `docs/service-layer-restructuring.md`
- `docs/code-quality-and-cleanup-roadmap.md`

### 6) Phase 2 Extraction Readiness

- [x] Define extraction boundary checklist for Celonis split.
- [x] Confirm all boundary tests green in full regression pack.
- [x] Publish extraction runbook draft.

Evidence:

- `docs/celonis-extraction-readiness-checklist.md`
- `docs/celonis-extraction-runbook-draft.md`

Documentation updates required:

- `docs/code-quality-and-cleanup-roadmap.md`
- `docs/domain-submodule-local-first-replatform.md`

## Latest Verification

- Targeted suites (Celonis + contracts): passing
- Multi-profile regression pack: passing
- Last known full artifact:
  - `./.orchestration/test-runs/profile-regression/regression-pack-20260510T145844Z.json`
