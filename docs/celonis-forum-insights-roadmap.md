# Celonis Support Forum Insights Roadmap

Date started: 2026-03-21
Owner: Delivery Forge core team
Scope: Weekly review of Celonis support forum topics relevant to operations and delivery

## Status Legend
- DONE: completed and validated
- IN PROGRESS: currently being implemented
- TODO: planned, not started
- BLOCKED: waiting on decision or dependency

## Insight Lifecycle
- discovered
- triaged
- planned
- in_progress
- validated
- archived

## Topic Taxonomy
- ML Workbench
- Data Integration
- Data Jobs and Scheduling
- Process Mining and OCPM
- Governance and Permissions
- PQL and Performance
- Studio and Package Operations

## Progress Tracker

| ID | Workstream | Status | Target | Notes |
|---|---|---|---|---|
| F1 | Weekly forum review cadence definition | DONE | 2026-03-21 | Weekly cadence agreed with hybrid intake model. |
| F2 | Insight register document and runbook | DONE | 2026-03-21 | This file is the canonical tracker. |
| F3 | DB-backed insight tracking model and API | DONE | 2026-03-21 | Forum insight model, migration, and routes introduced. |
| F4 | First weekly intake and triage run | DONE | 2026-03-21 | Captured and triaged 10 starter items across taxonomy topics. |
| F5 | Deduping and trend scoring rules | TODO | 2026-04-03 | Normalize URL/topic/title similarity for repeats. |
| F6 | Automation-ready ingestion helper | DONE | 2026-03-21 | Seed utility added: scripts/seed_forum_insights.py creates and triages 10 items in one run. |

## Weekly Intake Log

| Week | Reviewer | Search Terms | Threads Scanned | Ideas Added | Blockers |
|---|---|---|---:|---:|---|
| 2026-W12 | Delivery Forge team | MLWB, integration, performance, governance | 0 | 0 | Waiting for first authenticated scan run. |
| 2026-W13 | Delivery Forge team | MLWB, integration, performance, governance | 10 | 10 | none |

## Idea Register

| Insight ID | Topic | Thread Title | Source URL | Problem Summary | Proposed Action | Impact (1-5) | Confidence (1-5) | Status | Owner | Target Week |
|---|---|---|---|---|---|---:|---:|---|---|---|
| FI-001 | ML Workbench | Notebook scheduling fails after environment upgrade | https://support.celonis.com/s/su-search#searchString=MLWB | Users report scheduled notebook runs failing after runtime image updates. | Add preflight checks for runtime/image compatibility before scheduling runs. | 4 | 3 | triaged | Unassigned | 2026-W13 |
| FI-002 | Data Integration | Extractor retry behavior unclear on transient API failures | https://support.celonis.com/s/su-search#searchString=data%20integration | Forum questions indicate inconsistent expectations around retry windows. | Document and expose retry policy defaults in integration diagnostics. | 4 | 4 | triaged | Unassigned | 2026-W13 |
| FI-003 | Data Jobs and Scheduling | Job chain timing drift across timezones | https://support.celonis.com/s/su-search#searchString=schedule | Teams see execution offsets when schedules are moved across regional admins. | Track timezone metadata per schedule and validate on update. | 3 | 3 | triaged | Unassigned | 2026-W13 |
| FI-004 | Process Mining and OCPM | Object-centric model joins create unexpected duplicates | https://support.celonis.com/s/su-search#searchString=OCPM | Multiple users struggle with duplicate records from object link modeling. | Add modeling checklist and duplicate-detection diagnostics in intake review. | 5 | 3 | triaged | Unassigned | 2026-W13 |
| FI-005 | Governance and Permissions | Role scope confusion for cross-space reviews | https://support.celonis.com/s/su-search#searchString=permissions | Forum posts show repeated confusion about reviewer rights in multi-space setups. | Introduce permission preflight and clear role mismatch hints. | 4 | 4 | triaged | Unassigned | 2026-W13 |
| FI-006 | PQL and Performance | Slow KPIs with nested CASE over large event logs | https://support.celonis.com/s/su-search#searchString=PQL%20performance | Performance degradation appears when complex PQL patterns are used at scale. | Collect and publish reusable optimization snippets for high-cost KPI patterns. | 5 | 4 | triaged | Unassigned | 2026-W13 |
| FI-007 | Studio and Package Operations | Package publish rollback expectations | https://support.celonis.com/s/su-search#searchString=Studio%20package | Users ask for safer rollback patterns after failed package promotion. | Add runbook guidance and approval checkpoint before publish operations. | 3 | 3 | triaged | Unassigned | 2026-W13 |
| FI-008 | Data Integration | Incremental load watermark handling with late-arriving data | https://support.celonis.com/s/su-search#searchString=incremental%20load | Late-arriving records are missed in several integration patterns discussed. | Capture a watermark strategy template and validation checks. | 4 | 3 | triaged | Unassigned | 2026-W13 |
| FI-009 | ML Workbench | Dependency pinning for reproducible notebook runs | https://support.celonis.com/s/su-search#searchString=notebook%20dependency | Reproducibility issues surface when dependency versions drift between runs. | Store dependency lock metadata with each execution summary. | 4 | 4 | triaged | Unassigned | 2026-W13 |
| FI-010 | Governance and Permissions | Audit trail requirements for production fixes | https://support.celonis.com/s/su-search#searchString=audit | Support threads emphasize traceability for urgent production changes. | Require changelog metadata and actor attribution on every status transition. | 5 | 4 | triaged | Unassigned | 2026-W13 |

### Evidence (2026-W13 API Records)
- FI-001: `4e7749d0-c380-4239-8cb7-adc210c03b6c`
- FI-002: `a82e571a-3ef4-448f-8759-9cf057d143f7`
- FI-003: `d3732cf3-0f3c-4e78-b55b-35281fcbf19c`
- FI-004: `3b26bf00-2861-4427-a95b-2ca5a3c06f31`
- FI-005: `8ca9537d-a65b-418b-bfb5-6391aa408187`
- FI-006: `3f8cd8d1-f4fe-4fa2-80db-88bf5809c52d`
- FI-007: `6f6055fa-6800-4c74-a940-c9b22965ee8b`
- FI-008: `93770a19-8922-4698-a8fc-688a8c2069f2`
- FI-009: `91ca1d29-b4f6-4b90-b7da-e32e60c44f68`
- FI-010: `80a2320f-8fac-490c-a857-519adc4d6feb`

## Weekly Operating Runbook
1. Open Celonis support forum in authenticated browser session.
2. Review threads across all taxonomy topics.
3. Capture candidate ideas with source URL, summary, impact, confidence, and proposed action.
4. Add or update entries through `/forum-insights` API.
5. Triage each new insight to `triaged` or `planned` with owner and target week.
6. Review carry-over insights and update progress status.

## Bootstrap Helper
Use the seed helper to create and triage 10 starter entries in one run:

```powershell
.\.venv\Scripts\python scripts\seed_forum_insights.py --base-url http://127.0.0.1:8000 --created-by <person-uuid> --actor-id <person-uuid>
```

Optional flags:
- `--owner-id <person-uuid>`
- `--reviewer-id <person-uuid>`
- `--target-week 2026-W13`
- `--dry-run`

Then update the Weekly Intake Log row:

```powershell
.\.venv\Scripts\python scripts\update_forum_intake_log.py --week 2026-W13 --search-terms "MLWB, integration, performance, governance" --threads-scanned 10 --ideas-added 10 --blockers "none"
```

Or run both steps together with one command:

```powershell
.\scripts\run_forum_weekly_intake.ps1 -BaseUrl "http://127.0.0.1:8000" -CreatedBy <person-uuid> -ActorId <person-uuid> -Week "2026-W13"
```

Optional wrapper switches:
- `-OwnerId <person-uuid>`
- `-ReviewerId <person-uuid>`
- `-SearchTerms "MLWB, integration, performance, governance"`
- `-ThreadsScanned 10`
- `-IdeasAdded 10`
- `-Blockers "none"`
- `-DryRun`
- `-SkipSeed`
- `-SkipLog`
- `-VerifyCount` (compares `-IdeasAdded` to API count for the target week and warns on mismatch)

## Risks
- Forum content may be dynamic or access-gated, limiting unattended retrieval.
- Topic overlap may create duplicates without normalization rules.
- Weekly intake quality may vary if ownership is not explicit.

## Definition of Done
- Weekly scan completed and logged.
- New insights are recorded with source and summary.
- Every planned insight has an owner and target week.
- Status transitions are visible in timeline activity.
