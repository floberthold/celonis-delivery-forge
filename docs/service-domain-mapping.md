# Service Domain Mapping (Published)

Date: 2026-05-10
Source of truth: `config/service_domain_mapping.json`

## Purpose

Defines the initial service-to-domain allocation used to drive Phase 1b migration waves and reduce ambiguity in ownership.

## Domains

- platform
- delivery
- celonis
- knowledge
- integrations
- orchestration
- shared

## Current Mapping Snapshot

### platform

- feature_rollout.py

### delivery

- project_service.py
- review_service.py
- template_service.py
- template_seed.py
- todo_service.py
- activity_log.py
- florian_script_seed.py

### celonis

- celonis_contracts.py
- celonis_data_agent_service.py
- celonis_deployment_service.py
- celonis_payload_extractors.py
- snapshot_service.py
- snapshot_coverage_service.py
- snapshot_detail_extractors.py
- snapshot_export_service.py
- snapshot_git_service.py

### knowledge

- local_knowledge_gateway.py
- local_knowledge_control.py
- use_case_views.py

### integrations

- email_service.py
- ingest_service.py
- trycelonis_demo_rebuild.py

### orchestration

- quest_service.py

### shared

- (none yet)

## Notes

- This mapping is intentionally pragmatic for migration sequencing and can evolve as boundaries are refined.
- Changes must update both this document and `config/service_domain_mapping.json`.
