# Domain-Submodule Replatform (Local-First)

## Goal

Reduce runtime complexity without losing capabilities by running Delivery Forge as domain slices.

## Principles

- Local-first: all slices can run on a developer machine.
- Feature-complete by default: `full` profile keeps current behavior.
- Progressive rollout: pilot users start with a small slice and receive additional domains gradually.
- Stable contracts: each domain exposes explicit API/UI boundaries.

## Runtime Slices (Current)

- `core-platform`
  - Foundry API and core UI.
- `knowledge-hub`
  - Local wiki query API and Open WebUI adapter.
- `celonis-agent`
  - Celonis MCP and agent tooling.
- `data-utils`
  - Utility processes for data generation.
- `external-experiments`
  - Optional, non-core integrations and research utilities.

Domain mapping is maintained in `agentic/tool-hub/tool_hub_registry.json`.

## Activation Profiles

Profiles are maintained in `agentic/tool-hub/tool_hub_profiles.json`.

- `full`: all enabled tools.
- `pilot-core`: only `core-platform`.
- `pilot-core-plus-knowledge`: `core-platform` + `knowledge-hub`.
- `integration-celonis`: `core-platform` + `celonis-agent`.

## Rollout Model

1. Pilot A
- Profile: `pilot-core`
- Goal: validate baseline UX and workflows with lowest operational load.

2. Pilot B
- Profile: `pilot-core-plus-knowledge`
- Goal: add local knowledge workflows while keeping blast radius controlled.

3. Pilot C
- Profile: `integration-celonis`
- Goal: validate Celonis agent operations with selected users.

4. General Availability
- Profile: `full`
- Goal: all validated domains enabled.

Latest cross-profile verification artifact:

- `./.orchestration/test-runs/profile-regression/regression-pack-20260510T145844Z.json`

## Operational Commands

```powershell
# validate active slice without starting processes
.\START.ps1 -Mode dry-run -Profile pilot-core

# start selected slice
.\START.ps1 -Profile pilot-core-plus-knowledge

# inspect running processes
.\START.ps1 -Mode status

# stop all processes
.\START.ps1 -Mode stop
```

## Next Hardening Steps

- Add profile-aware health summary in Tool Hub status output. ✅ Completed (2026-05-10)
- Add per-profile acceptance test packs.
- Introduce profile-specific seed data for user testing. ✅ Completed (2026-05-10)
- Add in-app feature flags mirroring startup domains for finer UI gating.

## Integrated Execution Plan (Analysis-Aligned)

This plan integrates recommendations from:

- `READ_ME_FIRST.md`
- `QUICK_REFERENCE.md`
- `DELIVERABLES_MANIFEST.md`
- `REPOSITORY_ANALYSIS.md`
- `docs/code-analysis-complete-guide.md`
- `docs/code-quality-and-cleanup-roadmap.md`
- `docs/codebase-metrics-and-analysis.md`
- `docs/documentation-consolidation-plan.md`
- `docs/refactoring-ui-routes.md`
- `docs/service-layer-restructuring.md`

### Phase 1 (Contracts + Hardening) - Current Status

Completed:

- Domain/profile startup gating and activation-phase filtering for Tool Hub.
- Server-side route gating by rollout domain for Celonis and Knowledge UI.
- Profile startup/catalog contract tests and profile regression-pack automation.
- Celonis data-agent contract tests (including endpoint fallback behavior).
- Structured Celonis invoke-route errors with `error_code` + `request_id` payloads.
- Celonis adapter timeout/rate-limit/upstream error semantics.

Next in Phase 1:

- Standardize error classification constants and route adoption.
- Publish developer-facing API contract usage guide.
- Expand standardized health probe response semantics to additional specialized domains as extraction proceeds.

### Phase 1a (UI Route Refactoring) - Planned Tranche Order

1. Extract shared helpers from `src/foundry/api/routes/ui.py`.
2. Create route submodules under `src/foundry/api/routes/ui/`.
3. Move `navigation` and `integrations` routes first (highest coupling payoff).
4. Move `admin`, `templates`, and `health` routes.
5. Keep behavior unchanged and enforce parity tests per tranche.

### Phase 1b (Service Layer Restructuring) - Planned Tranche Order

1. Publish service-to-domain mapping document.
2. Add package scaffolding for `platform`, `delivery`, `celonis`, `knowledge`, `integrations`, `orchestration`, and `shared`.
3. Move lowest-risk services first (`email`, `feature_rollout`, `tool_hub`), then high-coupling services.
4. Maintain compatibility shims during migration to avoid broad import breakage.

### Phase 2 (Celonis Extraction) - Gating Criteria Before Repo Split

- Adapter boundaries and contracts are stable and test-backed.
- Error and observability semantics are standardized.
- End-to-end regression packs stay green across all profiles.
- Documentation and runbooks are updated before extraction cutover.

Readiness checklist:

- `docs/celonis-extraction-readiness-checklist.md`

## Documentation Sync Protocol

For every completed execution task:

1. Update the relevant implementation document (for example route/service/refactor/roadmap docs).
2. Update the consolidated roadmap status in `docs/code-quality-and-cleanup-roadmap.md`.
3. Update task state in `docs/replatform-implementation-tracker.md`.
4. Include test evidence and artifact paths when available.
