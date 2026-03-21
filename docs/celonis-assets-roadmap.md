# Celonis Asset Integration Roadmap

Date started: 2026-03-20
Owner: Delivery Forge core team
Source analyzed: [Code from Celonis](../Code%20from%20Celonis)

## Status Legend
- DONE: completed and validated
- IN PROGRESS: currently being implemented
- TODO: planned, not started
- BLOCKED: waiting on decision or dependency

## Progress Tracker

| ID | Workstream | Status | Target | Notes |
|---|---|---|---|---|
| R1 | Asset inventory and classification baseline | DONE | 2026-03-20 | Manifest created in [docs/celonis-asset-manifest.txt](celonis-asset-manifest.txt). |
| R2 | Pattern extraction and integration design | DONE | 2026-03-20 | Analysis documented in [docs/celonis-assets-analysis.md](celonis-assets-analysis.md). |
| R3 | Code-drop intake pipeline design | IN PROGRESS | 2026-03-24 | Added executable `/ingest/code-drop/execute` flow with folder scan, manifest persistence, snapshot/run creation, and automated findings. |
| R4 | Repo-sync intake mode design | IN PROGRESS | 2026-03-26 | Added `/ingest/repo-sync/execute` with branch/tag/commit provenance capture in snapshot summary metadata. |
| R5 | Secret scanning and compliance gate | TODO | 2026-03-27 | Block promotion on credential findings. |
| R6 | Notebook governance and metadata capture | TODO | 2026-03-31 | Add notebook asset type and provenance fields. |
| R7 | Endpoint profile registry for Celonis actions | TODO | 2026-04-02 | Replace free-form paths where possible. |
| R8 | Diagnostics persistence and UI timeline visibility | TODO | 2026-04-05 | Persist pipeline and integration diagnostics. |
| R9 | Pilot integration on one imported package | TODO | 2026-04-09 | Start with dm-load-optimization subset. |
| R10 | Team operating model and handoff guide | TODO | 2026-04-12 | Document role split for code-drop onboarding. |

## Phase Plan

### Phase 0: Baseline (Completed)
- [x] Build inventory of incoming Celonis assets.
- [x] Extract architectural and process patterns.
- [x] Document integration options and governance implications.

### Phase 1: Intake Foundation
- [x] Define ingestion entities:
  - asset_source
  - asset_snapshot
  - ingest_run
  - ingest_finding
- [x] Create API contracts for code-drop ingestion and status retrieval.
- [x] Store immutable source manifest for each drop.

### Phase 2: Risk and Governance Controls
- [x] Add secret scanning rules for common token formats.
- [ ] Add policy check status to review workflow.
- [ ] Require remediation state before promotion.

### Phase 3: Integration Acceleration
- [ ] Build endpoint profile templates for common Celonis operations.
- [ ] Add notebook asset metadata and ownership workflow.
- [ ] Add diagnostics model and timeline rendering.

### Phase 4: Operationalization
- [ ] Pilot with one real code drop and measure cycle time.
- [ ] Add regression tests for ingestion/policy gates.
- [ ] Publish a team runbook for drop vs pull workflows.

## Weekly Tracking Template
Use this table during implementation weeks.

| Week | Focus | Planned | Done | Risks | Decision Needed |
|---|---|---|---|---|---|
| 2026-W12 | Baseline and design | Inventory + roadmap | Completed | Token handling in imported configs | Decide quarantine behavior |
| 2026-W13 | Intake foundation | R3-R4 |  |  |  |
| 2026-W14 | Governance controls | R5-R6 |  |  |  |
| 2026-W15 | Integration acceleration | R7-R8 |  |  |  |
| 2026-W16 | Pilot and hardening | R9-R10 |  |  |  |

## First Risk Register
- Security: token-like secret present in imported config files.
- Quality: notebooks dominate over packaged modules for some workflows.
- Operability: inconsistent setup paths across drops (manual notebook setup vs formal service template).
- Dependency risk: internal/private package assumptions in bootstrapper template.

## Definition of Done for This Roadmap
- Intake flows exist for both drop and pull modes.
- Every imported asset has provenance, owner, and review status.
- Secret findings are blocking until resolved.
- At least one imported package is partially productized under the Foundry architecture.
