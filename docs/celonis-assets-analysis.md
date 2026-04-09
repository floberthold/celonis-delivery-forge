# Celonis Asset Analysis and Integration Playbook

## Scope
This document analyzes the code drop in [Code from Celonis](../Code%20from%20Celonis) and extracts patterns we can integrate into the Delivery Forge platform.

## Asset Snapshot (2026-03-20)
- Total files (excluding .git internals): 229
- Main types:
  - 125 Python files
  - 17 notebooks
  - 24 YAML files
  - 2 OpenAPI JSON files + 1 top-level Swagger JSON
- Main groups:
  - [Code from Celonis/dm-load-optimization](../Code%20from%20Celonis/dm-load-optimization)
  - [Code from Celonis/image-processing](../Code%20from%20Celonis/image-processing)
  - [Code from Celonis/Independent_Requirement_Script](../Code%20from%20Celonis/Independent_Requirement_Script)
  - [Code from Celonis/KPI_Resolver](../Code%20from%20Celonis/KPI_Resolver)
  - [Code from Celonis/m-20-ocpm-bootstrapper-main](../Code%20from%20Celonis/m-20-ocpm-bootstrapper-main)
- Full inventory: [docs/celonis-asset-manifest.txt](celonis-asset-manifest.txt)

## What We Learned from Their Patterns

### 1) Notebook-first delivery for practitioner workflows
Observed in:
- [Code from Celonis/dm-load-optimization/README.md](../Code%20from%20Celonis/dm-load-optimization/README.md)
- Multiple notebooks under dm-load-optimization, image-processing, and bootstrapper folders.

Pattern:
- Operational work is often delivered as runbooks + notebooks first, then partially productized into Python packages.

Implication for Delivery Forge:
- Treat notebooks as first-class assets in intake/review workflows.
- Require a minimal metadata envelope for notebook assets (owner, tenant, risk, dependencies, expected outputs).

### 2) Domain-sliced service architecture
Observed in:
- [Code from Celonis/m-20-ocpm-bootstrapper-main/m-20-ocpm-bootstrapper-main/README.md](../Code%20from%20Celonis/m-20-ocpm-bootstrapper-main/m-20-ocpm-bootstrapper-main/README.md)

Pattern:
- FastAPI app organized by feature/domain with dedicated tests (unit/integration/e2e), client generation, and OpenAPI contracts.

Implication for Delivery Forge:
- Expand existing route/service split in [src/foundry/api](../src/foundry/api) and [src/foundry/services](../src/foundry/services) toward domain modules per integration capability.
- Add stronger contract-first integration to Celonis APIs (per-service endpoint profiles).

### 3) Graph/pipeline-oriented extraction architecture
Observed in:
- [Code from Celonis/image-processing/document_extraction_pipeline/core/main.py](../Code%20from%20Celonis/image-processing/document_extraction_pipeline/core/main.py)
- [Code from Celonis/image-processing/document_extraction_pipeline/config.yaml](../Code%20from%20Celonis/image-processing/document_extraction_pipeline/config.yaml)

Pattern:
- Explicit state object, graph execution, diagnostics collection, staged extraction, confidence-based performance decisions.

Implication for Delivery Forge:
- Build ingestion pipelines as stateful stages with diagnostics and decision metadata.
- Persist processing diagnostics in a dedicated model/table to improve observability and governance.

### 4) Environment-specific deployment and service contracts
Observed in:
- [Code from Celonis/m-20-ocpm-bootstrapper-main/m-20-ocpm-bootstrapper-main/resources](../Code%20from%20Celonis/m-20-ocpm-bootstrapper-main/m-20-ocpm-bootstrapper-main/resources)
- [Code from Celonis/m-20-ocpm-bootstrapper-main/m-20-ocpm-bootstrapper-main/SETUP.md](../Code%20from%20Celonis/m-20-ocpm-bootstrapper-main/m-20-ocpm-bootstrapper-main/SETUP.md)

Pattern:
- Separate environment overlays, generated clients from OpenAPI specs, and explicit infra onboarding steps.

Implication for Delivery Forge:
- Introduce profile-based connection templates for tenant environment classes (sandbox, dev, prod-like).
- Store API endpoint profiles as reusable templates linked to client and project context.

### 5) Security hygiene gaps in ad-hoc drops
Observed in:
- [Code from Celonis/dm-load-optimization/config.yaml](../Code%20from%20Celonis/dm-load-optimization/config.yaml)

Pattern:
- A token appears hardcoded in config data in the drop.

Implication for Delivery Forge:
- Add automatic secret scanning and quarantine at import time.
- Block promotion of assets flagged with possible credentials until remediated.

## Integration Opportunities into Current App
Current baseline:
- Celonis connection + extract/import is already available in [src/foundry/api/routes/celonis.py](../src/foundry/api/routes/celonis.py) and [src/foundry/integrations/celonis_import.py](../src/foundry/integrations/celonis_import.py).

Recommended next integrations:
1. Asset Intake Pipeline
- Add a new intake flow for code drops and pulled repos.
- Parse manifests, infer asset types, compute risk signals, and store metadata.

2. Notebook Governance
- Register notebooks as assets with review requirements.
- Capture notebook execution provenance (kernel, packages, last run timestamp, output artifacts).

3. Endpoint Profile Registry
- Build reusable endpoint profiles for common Celonis API actions.
- Replace free-form path usage with approved profiles where possible.

4. Diagnostics and Observability
- Introduce structured diagnostics persistence for imports/extracts and future document/pipeline jobs.
- Expose diagnostics in timeline/activity views.

5. Secret and Compliance Controls
- Add pre-ingest and pre-promotion checks for tokens, keys, and forbidden patterns.
- Surface blocking findings directly in review workflow.

## Methodology for Managing Incoming Assets

### Intake Modes
1. Code Drop Mode (most frequent)
- Receive zip/folder
- Create immutable snapshot manifest
- Run classification + risk scan
- Register assets and assign owners/reviewers

2. Pullable Repo Mode
- Mirror or shallow-clone source
- Record branch/tag/commit provenance
- Run same classification + risk scan
- Sync deltas on schedule or manually

### Standard Workflow (both modes)
1. Discover: Inventory files and classify by asset type.
2. Secure: Secret/license/compliance checks.
3. Normalize: Move reusable code to package modules, keep notebooks as orchestration/exploration.
4. Govern: 4-eyes review with explicit acceptance criteria.
5. Operationalize: Add tests, diagnostics, and runbook.
6. Track: Add status in roadmap and timeline.

## Concrete Backlog Seeds
- Asset type extension: notebook, openapi_spec, pipeline_config, prompt_pack, test_cassette.
- New entities: asset_source, asset_snapshot, ingest_run, ingest_finding.
- New API routes: /ingest/code-drop, /ingest/repo-sync, /ingest/runs, /ingest/findings.
- Policy checks: secret patterns, large binary checks, dependency metadata completeness.

## Immediate Actions Taken
- Created inventory file: [docs/celonis-asset-manifest.txt](celonis-asset-manifest.txt)
- Created roadmap and tracker: [docs/celonis-assets-roadmap.md](celonis-assets-roadmap.md)

## Notes
- Use placeholders for all credentials in imported configs.
- Keep dropped source immutable under a dedicated folder; build normalized production code under [src/foundry](../src/foundry).
