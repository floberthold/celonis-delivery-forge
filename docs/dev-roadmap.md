# Developer Roadmap

## Purpose
This document is the engineering execution roadmap for Celonis Delivery Forge.
It focuses on backend, UI, data model, integration reliability, and developer productivity.

## Horizon
- Timeframe: 6 months (rolling)
- Last updated: 2026-03-21
- Owner: Engineering Lead

## Status Legend
- Planned: Defined but not started
- In Progress: Actively being implemented
- In Review: Code complete, under testing/review
- Done: Released and validated
- Blocked: Waiting on dependency or decision

## Phase 1: Platform Stability (Weeks 1-4)
Status: In Progress

Goals:
- Stabilize auth/session handling across API and UI routes.
- Complete migration consistency checks and DB startup validation.
- Add baseline health and diagnostics pages for operations.

Deliverables:
- Consistent auth dependency usage in UI and API paths.
- Verified alembic migration chain with rollback notes.
- Documented local/dev bootstrap in README.

Success criteria:
- No critical auth regressions in manual smoke tests.
- Clean startup and migration on a fresh database.

## Phase 2: Delivery Workflow Hardening (Weeks 5-8)
Status: Planned

Goals:
- Improve project/review/todo workflow correctness and guardrails.
- Strengthen activity logging coverage for key business actions.
- Improve review and todo lifecycle visibility in UI.

Deliverables:
- Service-layer validation for project/review/todo transitions.
- End-to-end traceability for create/update/delete actions.
- UI health indicators for delayed reviews and overdue tasks.

Success criteria:
- Core workflows pass regression scenarios.
- Timeline data is sufficient for operational auditing.

## Phase 3: Celonis Integration Maturity (Weeks 9-14)
Status: Planned

Goals:
- Expand from endpoint-driven actions to guided integration flows.
- Add robust connection diagnostics and failure handling.
- Improve visibility for data pipeline and automation reliability.

Deliverables:
- Connection and API preflight checks surfaced in UI.
- Structured error categories and user-actionable remediation.
- Integration metrics in client/project health views.

Success criteria:
- Integration errors are diagnosable without code inspection.
- Reduced manual troubleshooting effort for tenant actions.

## Phase 4: Quality and Automation (Weeks 15-20)
Status: Planned

Goals:
- Build reliable test coverage for services and route layers.
- Add lint/type/test gates for CI readiness.
- Reduce defects caused by schema and enum drift.

Deliverables:
- Unit tests for service modules and validation rules.
- API route tests for high-risk endpoints.
- Standardized pre-merge quality checks.

Success criteria:
- Reproducible green test run in CI and local environments.
- Fewer regressions in workflow-critical areas.

## Phase 5: Developer Experience and Scale (Weeks 21-24)
Status: Planned

Goals:
- Improve modularity and maintainability of large route modules.
- Reduce coupling between UI handlers and domain logic.
- Speed up onboarding and implementation throughput.

Deliverables:
- Route/service refactor plan with phased extraction.
- Shared helpers for query filtering and table rendering contexts.
- Clear engineering docs for architecture and extension points.

Success criteria:
- Smaller, easier-to-review change sets.
- Faster implementation time for new features.

## Cross-Cutting Workstreams
- Security: cookie/session hardening, permission checks, audit visibility.
- Observability: better error messages, operational diagnostics, activity metadata quality.
- Documentation: keep roadmap, architecture decisions, and runbooks current.

## Dependencies and Risks
- Celonis API behavior and credential management constraints.
- Scope growth from UI feature requests without backend capacity.
- Existing large in-flight change set in the repository.

## Update Cadence
- Weekly: update status and blockers.
- Biweekly: re-prioritize based on defects and customer impact.
- Monthly: adjust the rolling 6-month horizon.
