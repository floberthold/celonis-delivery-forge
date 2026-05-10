# Agent Feature Roadmap: Celonis Coverage

## Purpose
This document is the canonical feature-coverage map for Celonis capabilities in Celonis Delivery Forge. Agents should use it to determine what is already implemented, what is only partially implemented, and what is still planned.

## Scope
- In scope: Celonis connectivity, extract/import workflows, Data Integration, Studio, query/export, governance wrappers, and operational controls.
- Out of scope: generic project-management features unrelated to Celonis integration.

## Current Coverage (Implemented)
- Tenant connection persistence and upsert flow.
  Evidence: src/foundry/api/routes/celonis.py, src/foundry/models.py.
- Basic Celonis API pass-through actions (extract/import).
  Evidence: src/foundry/api/routes/celonis.py, src/foundry/integrations/celonis_import.py.
- Typed Celonis data-agent catalog and governed invoke API for discovery, SQL analysis, and deployment-gated Studio write actions.
  Evidence: src/foundry/api/routes/celonis.py, src/foundry/services/celonis_data_agent_service.py, tests/test_celonis_user_token_api.py.
- Deployment request lifecycle API with reviewer assignment, approval queue listing, detailed history timeline, and Tool Hub UI for invoking typed Celonis tools from Foundry.
  Evidence: src/foundry/api/routes/celonis_deployments.py, src/foundry/services/celonis_deployment_service.py, src/foundry/ui/templates/celonis_tool_hub.html, tests/test_celonis_deployments_api.py, tests/test_celonis_tool_hub_ui.py.
- Dashboard controls for manual Celonis actions and tenant binding.
  Evidence: src/foundry/ui/templates/dashboard.html.
- Activity logging for connection create/update events.
  Evidence: src/foundry/services/activity_log.py, src/foundry/api/routes/ui.py.
- Connection preflight diagnostics endpoint and dashboard trigger with service-scoped permission checks, batch execution, and persisted history.
  Evidence: src/foundry/api/routes/celonis.py, src/foundry/api/routes/ui.py, src/foundry/integrations/celonis_import.py, src/foundry/services/activity_log.py, src/foundry/ui/templates/dashboard.html.

## Partial Coverage
- Celonis integration is available but still mostly endpoint/path-driven actions.
  Gap: no typed object browser or guided workflows.
- Governance model exists globally, but Celonis operations are not fully modeled as reviewable change objects.
  Gap: limited approval gating at operation granularity.
- Studio write actions are available through deployment-gated data-agent tools, but the UI and deployment execution path are still thin.
  Gap: no dedicated Studio authoring UI, limited endpoint normalization, and no supervised publish replay worker.

## Gaps (Not Yet Implemented)
### Auth and Security
- Multi-credential auth modes (OAuth client credentials, APP_KEY/USER_KEY orchestration).
- Permission introspection and preflight diagnostics by service/scope.
- Per-connection credential storage and rotation metadata.

### Data Integration
- Managed lifecycle for data pools, models, jobs, and tasks.
- Transformation statement management and execution polling UI.
- Scheduled sync templates, retries, and rollback metadata.

### Studio and App Lifecycle
- Space/package/asset creation workflow in Forge.
- Package publish/version compare and promotion controls.
- Published-app explorer with governed release flow.

### Query and Export
- Guided PQL/SaolaPy workbench with validation and preview.
- Analysis/knowledge-model component discovery and one-click data extraction.

### Operations
- Rate-limit handling visibility, health dashboards, and SLA alerting.
- Integration contract tests and permission-edge-case test matrix.

### AI Assistance (Optional)
- pycelonis_llm-powered assistant for query authoring and explanation, with admin toggle and audit controls.

## Roadmap Phases
1. Foundation and safety: auth diagnostics, permission preflight, object discovery.
2. Governed Data Integration: jobs/tasks lifecycle, execution tracking, schedulers.
3. Studio release governance: package workflows, publishing, versioning, promotion.
4. Query acceleration: PQL/SaolaPy workbench and reusable snippets.
5. Operational maturity: observability, automated tests, policy hardening.
6. Optional intelligence: LLM assistant with strict governance and logging.

## Coverage Matrix
| Capability | Status | Evidence | Next step |
|---|---|---|---|
| Tenant connection storage | covered | src/foundry/models.py | Add credential types and rotation metadata |
| Connection upsert/list APIs | covered | src/foundry/api/routes/celonis.py | Add permission preflight response details |
| Basic extract/import actions | covered | src/foundry/api/routes/celonis.py, src/foundry/integrations/celonis_import.py | Replace free-form paths with typed actions |
| Dashboard Celonis cards | covered | src/foundry/ui/templates/dashboard.html | Add richer diagnostics and execution widgets |
| Audit of connection events | covered | src/foundry/services/activity_log.py, src/foundry/api/routes/ui.py | Expand to extract/import/job/task/publish events |
| Typed data-agent discovery and invoke API | covered | src/foundry/api/routes/celonis.py, src/foundry/services/celonis_data_agent_service.py, src/foundry/ui/templates/celonis_tool_hub.html, tests/test_celonis_user_token_api.py, tests/test_celonis_tool_hub_ui.py | Add richer output rendering and saved tool recipes |
| Connection preflight probe | covered | src/foundry/api/routes/celonis.py, src/foundry/api/routes/ui.py, src/foundry/integrations/celonis_import.py, src/foundry/services/activity_log.py | Add trend dashboards and alert thresholds |
| Data pool/model/job management | not-covered | n/a | Implement managed CRUD with approvals |
| Job task SQL workflow | not-covered | n/a | Add create/update/enable/disable/execute endpoints + polling |
| Studio package lifecycle | partial | src/foundry/api/routes/celonis.py, src/foundry/api/routes/celonis_deployments.py, src/foundry/services/celonis_data_agent_service.py, src/foundry/services/celonis_deployment_service.py, tests/test_celonis_user_token_api.py, tests/test_celonis_deployments_api.py | Add reviewer SLA dashboards and execution tracking for approved deployment runs |
| Analysis/KM guided export | not-covered | n/a | Add discovery flow and export templates |
| PQL/SaolaPy workbench | not-covered | n/a | Add query validation/preview and snippet registry |
| LLM assistant | not-covered | n/a | Add opt-in assistant with audit trail |

## Agent Update Rules
- When a Celonis-related feature is merged, update this file in the same change set.
- Change status only with concrete evidence paths.
- If status moves to covered, include backend and user-accessible path evidence.
- Keep Next step actionable and concise.
- Update the date in Last Reviewed.

## Last Reviewed
- Date: 2026-05-10
- Reviewer: GitHub Copilot (GPT-5.4)
- Basis: repository scan + Studio write-tool deployment governance update
