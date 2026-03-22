# Celonis Snapshot Coverage Matrix

This matrix maps requested Celonis artifact families to the snapshot extractor and persisted entities.
Scope aligns with public API surfaces used by this repository and PyCelonis EMS domains (Studio, Apps, Data Integration, Process/Knowledge).

## Coverage Summary

| Artifact family | Capture path | Persistence model | Current status |
| --- | --- | --- | --- |
| Spaces | `/package-manager/api/spaces`, `/studio/api/spaces` | `SnapshotSpace` | Covered |
| Packages | `/package-manager/api/packages` | `SnapshotPackage` | Covered |
| Package assets (KPI, View, Analysis, Annotation Builder, Action Flow, Skill, Simulation, etc.) | `/package-manager/api/packages/{package_key}/assets` | `SnapshotTask` with `task_type` | Covered |
| Apps | `/apps/api/packages`, `/apps/api/apps` | `SnapshotApp` | Covered |
| Data models | `/process-mining/api/data-models`, `/integration/api/v1/data-models` | `SnapshotDataModel` | Covered |
| Data pools | `/integration/api/pools`, `/integration/api/v1/pools` | `SnapshotDataPool` | Covered |
| Transformations | `/integration/api/v1/transformations`, `/integration/api/transformations`, per-pool variants | `SnapshotTransformation` | Covered |
| Jobs | `/integration/api/v1/jobs`, `/integration/api/jobs` | `SnapshotJob` | Covered |
| Knowledge models | `/knowledge-model/api/knowledge-models`, `/semantic-layer/api/knowledge-models` | `SnapshotKnowledgeModel` | Covered |

## Notes

- "Everything" in this implementation means everything available via authenticated tenant APIs and permissions.
- Package-contained objects are captured as tasks with typed discrimination through `task_type`.
- Snapshot summary now includes:
  - `task_types` counts for visibility into extracted package asset types.
  - `coverage` stats with endpoint attempts and endpoint hits per artifact family.
- Multi-endpoint extraction and simple pagination traversal are enabled to reduce missing assets from large tenants.

## Operational Validation

After running `/snapshots/trigger`, inspect `summary_json` and verify:

- Non-zero family counts where expected.
- `coverage.*.endpoints_with_data` indicates at least one successful endpoint per family.
- `task_types` contains expected values (for example `KPI`, `ACTION_FLOW`, `ANALYSIS`, `ANNOTATION_BUILDER`, `SKILL`).

If a family remains empty despite tenant content, check token scope/permissions and endpoint availability for that tenant release.