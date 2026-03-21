# Celonis-Informed Roadmap (6-Month Rolling)

## Purpose
This roadmap translates Celonis documentation themes into an executable plan for this repository over a rolling 6-month horizon.

## Source Inputs
- Celonis Getting Started: https://docs.celonis.com/en/getting-started-with-the-celonis-platform.html
- Celonis Docs Index: https://docs.celonis.com/index.html?lang=en

## Scope
In scope:
- Platform/team setup and governance model
- Data integration and ingestion priorities
- Objects and Events modeling baseline
- Studio apps, dashboards, and PQL KPI enablement
- Automation and operational governance

Out of scope:
- Guaranteed feature availability beyond project license
- Vendor roadmap commitments not yet generally available

## Status Legend
- Planned: Defined but not started
- In Progress: Active work with owner and target window
- Done: Completed with evidence links
- Blocked: Cannot proceed due to an explicit blocker

## Operating Cadence
- Weekly: Move items between Kanban sections.
- Biweekly: Review milestone health, risks, and dependencies.
- Monthly: Re-balance the rolling 6-month horizon.

## Horizon and Phases
Planning window: 2026-03-20 to 2026-09-30

### Phase 1 (Weeks 1-4): Foundations
Goals:
- Confirm team roles, access model, and governance gates.
- Define source-system onboarding priority list.

### Phase 2 (Weeks 5-10): Data and Modeling
Goals:
- Implement ingestion sequence and quality gates.
- Establish Object/Event model and initial KPI/PQL baseline.

### Phase 3 (Weeks 11-16): Apps and Insights
Goals:
- Deliver Studio-facing views for core business questions.
- Add action loops (alerts/tasks) tied to KPI thresholds.

### Phase 4 (Weeks 17-24): Scale and Operationalize
Goals:
- Harden security/compliance operational checks.
- Establish release governance and next-horizon backlog.

## Milestone Map
| Milestone | Target Window | Primary Owner | Dependencies | Exit Criteria |
|---|---|---|---|---|
| M1. Governance and access baseline | W1-W2 | TBD | None | Roles, permissions, and approval gates documented |
| M2. Data source onboarding plan | W2-W4 | TBD | M1 | Prioritized source list with ingestion sequence approved |
| M3. Object/Event modeling baseline | W5-W7 | TBD | M2 | Canonical model documented and validated on pilot data |
| M4. KPI/PQL baseline pack | W7-W10 | TBD | M3 | Initial KPI library and query set reviewed |
| M5. Studio insight slice v1 | W11-W13 | TBD | M4 | First role-based dashboard/app released |
| M6. Action loop integration | W13-W16 | TBD | M5 | Alert/task workflow connected to KPI thresholds |
| M7. Operational hardening | W17-W20 | TBD | M6 | Runbook, security checks, and release cadence active |
| M8. Roll-forward plan | W21-W24 | TBD | M7 | Next 6-month roadmap drafted with carry-over decisions |

## Kanban Progress Tracker

### Planned
- [ ] R-001 Define ownership matrix and governance gate checklist
  - Owner: TBD
  - Target: 2026-W1
  - Depends on: None
  - Acceptance criteria: Ownership matrix approved by stakeholders.
  - Evidence: docs link, approval note link

- [ ] R-002 Create data source inventory and prioritize onboarding waves
  - Owner: TBD
  - Target: 2026-W2
  - Depends on: R-001
  - Acceptance criteria: Source inventory with wave assignments and rationale.
  - Evidence: inventory file link, review note link

- [ ] R-003 Define canonical Object/Event model for first process domain
  - Owner: TBD
  - Target: 2026-W6
  - Depends on: R-002
  - Acceptance criteria: Model reviewed, entities and relations finalized.
  - Evidence: model doc link, validation output link

- [ ] R-004 Deliver initial KPI/PQL pack for pilot analysis
  - Owner: TBD
  - Target: 2026-W9
  - Depends on: R-003
  - Acceptance criteria: KPI definitions and PQL queries validated with business owners.
  - Evidence: query repo link, validation report link

- [ ] R-005 Publish first Studio dashboard/app slice
  - Owner: TBD
  - Target: 2026-W12
  - Depends on: R-004
  - Acceptance criteria: Dashboard/app accessible to target user group with sign-off.
  - Evidence: release note link, screenshot/demo link

- [ ] R-006 Add action loop for KPI threshold breach handling
  - Owner: TBD
  - Target: 2026-W15
  - Depends on: R-005
  - Acceptance criteria: Triggered workflow verified end-to-end in test scenario.
  - Evidence: run log link, workflow config link

- [ ] R-007 Establish monthly release and review rhythm
  - Owner: TBD
  - Target: 2026-W18
  - Depends on: R-006
  - Acceptance criteria: Recurring review ceremony and agenda running.
  - Evidence: calendar link, notes link

- [ ] R-008 Prepare next rolling 6-month plan
  - Owner: TBD
  - Target: 2026-W24
  - Depends on: R-007
  - Acceptance criteria: Next roadmap approved with carry-over and new initiatives.
  - Evidence: next roadmap link

### In Progress
- [ ] No active items yet

### Done
- [x] R-000 Roadmap initialization and tracker setup
  - Completed: 2026-03-20
  - Evidence: docs/roadmap-celonis.md

- [x] D-001 Initial project governance criteria documented
  - Completed: 2026-03-20 (existing)
  - Evidence: README.md

- [x] D-002 Incremental collaboration milestones already demonstrated in schema history
  - Completed: 2026-03-20 (existing)
  - Evidence: alembic/versions/20260302_0001_add_template_tables.py
  - Evidence: alembic/versions/20260303_0002_add_todo_table.py
  - Evidence: alembic/versions/20260319_0003_expand_todo_collaboration.py

- [x] D-003 UI-level task tracking pattern already present
  - Completed: 2026-03-20 (existing)
  - Evidence: src/foundry/ui/templates/todos.html

### Blocked
- [ ] B-001 Placeholder for external blockers
  - Blocker: None currently recorded
  - Next review: 2026-W1

## Movement Rules
- Planned -> In Progress requires owner, target window, and dependency check.
- In Progress -> Done requires acceptance criteria met and at least one evidence link.
- Any -> Blocked requires explicit blocker description and next review date.
- Done items should only change to add missing evidence links.

## Risk Register
- License mismatch risk: Some documented Celonis features may not be enabled in this tenant.
- Data readiness risk: Source quality and latency may delay modeling milestones.
- Adoption risk: Dashboard release without role-specific onboarding may reduce usage.

## Update Log
- 2026-03-20: Created roadmap, seeded milestones, and completed tracker initialization task (R-000).
