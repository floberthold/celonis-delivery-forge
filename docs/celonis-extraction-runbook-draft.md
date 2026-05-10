# Celonis Extraction Runbook (Draft)

Date: 2026-05-10
Owner: Platform Engineering
Status: Draft for Phase 2

## Objective

Define a repeatable procedure to extract Celonis-focused capabilities into an isolated boundary while preserving current API behavior and rollback safety.

## Scope

- Celonis route surface and supporting service modules.
- Snapshot, deployment, and data-agent integrations.
- Existing non-Celonis delivery and UI routes stay in place.

## Preconditions

- Phase 1 contract standardization is complete.
- UI route decomposition reached stable, test-backed slices.
- Low-risk service migration and compatibility shims are in place.
- Regression pack and targeted suites are green.

## Entry Criteria

1. Service domain map is current.
2. Boundary checklist is current in docs/celonis-extraction-readiness-checklist.md.
3. No unresolved critical regressions in Celonis routes.

## Execution Steps

1. Freeze extraction branch
- Create a dedicated extraction branch from main.
- Freeze unrelated refactors while extraction is active.

2. Lock contract and error semantics
- Verify response contracts and error payloads are unchanged for public Celonis endpoints.
- Capture baseline OpenAPI snippets for Celonis routes.

3. Build dependency inventory
- List all imports for Celonis boundary services and routes.
- Classify each dependency as boundary-internal or cross-domain.

4. Isolate service modules
- Keep canonical Celonis services under src/foundry/services/celonis.
- Remove direct cross-domain coupling from Celonis modules where possible.
- Replace unavoidable cross-domain calls with explicit gateway functions.

5. Isolate route wiring
- Ensure Celonis route modules only import Celonis boundary services and shared contracts.
- Avoid importing delivery-domain internals from Celonis routes.

6. Validate data persistence assumptions
- Verify table usage and migrations for Celonis snapshots and deployment workflows.
- Confirm no schema assumptions depend on removed in-process helpers.

7. Run verification suite
- Run targeted Celonis/API/UI suites.
- Run shim parity and routing presence checks.
- Run profile regression pack if available.

8. Capture extraction artifact
- Store test logs and a short extraction report in .orchestration/test-runs.
- Document known warnings separately from failures.

9. Rollback plan
- Keep a rollback commit/tag before boundary cutover.
- Define one-command rollback procedure to restore previous router/service wiring.

## Verification Matrix

- Celonis route behavior parity: required
- Error payload parity: required
- Snapshot and deployment flows: required
- UI route presence checks: required
- Service shim parity: required until high-coupling cutover completes

## Exit Criteria

1. Celonis boundary tests pass.
2. No unresolved route regressions.
3. Tracker and roadmap docs updated with evidence links.
4. Rollback command verified on extraction branch.

## Risks and Mitigations

- Risk: hidden import coupling
- Mitigation: pre-extraction import inventory and route-level smoke tests

- Risk: behavior drift in error responses
- Mitigation: contract tests and baseline payload snapshots

- Risk: migration-only breakages
- Mitigation: run extraction validation in clean environment and with seeded data

## Evidence Template

- Branch: <name>
- Baseline commit: <sha>
- Validation command: <command>
- Result summary: <pass/fail + counts>
- Artifact paths: <paths>
- Rollback command: <command>
