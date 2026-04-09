# Use-Case Library — Product Roadmap

> **Horizon:** 6 months (March – September 2026)  
> **Owner:** Delivery Lead  
> **Last updated:** 2026-03-21  
> **Status key:** `🔲 Planned` · `🔵 In Discovery` · `🟡 In Build` · `🟠 In Review` · `✅ Released` · `🚫 Blocked`

---

## Vision

A single, searchable use-case hub connected to every project, client, industry, and person in
Celonis Delivery Forge — with four controlled visibility modes so the right level of detail reaches
the right audience without manual redaction overhead.

| View | Audience | Client names shown | KPI detail | Access control |
|---|---|---|---|---|
| **Internal detailed** | Delivery team | ✅ Full | ✅ Full | JWT role = admin or lead |
| **Client-only portal** | Account team + client | ✅ Own client only | ✅ Own client only | Client-scoped JWT or token |
| **Anonymized public** | Anyone (partner / prospect) | ❌ Suppressed | ❌ Rounded | Public (no auth) |
| **Industry benchmark** | Any authenticated user | ❌ Suppressed | Aggregated only | JWT authenticated |

---

## Taxonomy (Canonical Categories)

Derived from https://developer.celonis.com/use-cases/ and delivery project patterns.

| # | Category | Sub-themes | Celonis API surface |
|---|---|---|---|
| 1 | **3P Enrichment** | Process scores · anomaly flags · task-level status · recommendations | Knowledge Model API |
| 2 | **Analytics Export / BI** | KPI sharing · digital transformation impact · self-discoverable metadata · OData protocol | Knowledge Model API · OData |
| 3 | **Automation Triggers** | Inefficiency-triggered procedures · anomaly events · new-case events | Knowledge Model API · Subscription API |
| 4 | **Live Sync** | Dashboard refresh · data-lake sync | Knowledge Model API |
| 5 | **AI Agent – Tool Execution** | Informative retrieval tools · actionable execution tools | AI Agent API · MCP |
| 6 | **AI Agent – Chat** | Scoped conversational agents in 3P apps | AI Agent API |
| 7 | **Semantic Tool Generation** | OpenAPI spec from KM · column stats · semantic query | Knowledge Model API (beta) |
| 8 | **Operational Recommendations** | Task/activity guidance for frontline users | Knowledge Model API · Action Flows |
| 9 | **Industry Process Patterns** | Cross-client reusable process blueprints | Internal (Forge) |

## Action-Flow Template Library Mapping (April 2026)

The Make-inspired action-flow template starter pack is implemented in:
- `developer/action_flow_templates/schema/action-flow-template.schema.json`
- `developer/action_flow_templates/specs/`
- `developer/action_flow_templates/playbooks/`

### Family to Taxonomy Mapping

| Template family | Primary taxonomy categories | Starter templates |
|---|---|---|
| Alerts and Escalation | Automation Triggers, Operational Recommendations | KPI threshold alert, anomaly escalation chain, data quality stopline |
| Sync and Propagation | Live Sync, Analytics Export / BI | Nightly KM recommendation sync, subscription event materialized sync, weekly steering pack refresh |
| Recommendation and Human Loop | Operational Recommendations, Industry Process Patterns | Recommendation approval gate, priority case auto routing, action effectiveness feedback |
| AI-Assisted Triage | AI Agent - Tool Execution, AI Agent - Chat | Low-confidence triage review loop, client comms draft, incomplete execution watchdog |

### Delivery Priority
1. Pilot one alerts template and one sync template first.
2. Expand to recommendation human-loop templates for high-impact processes.
3. Roll out AI-assisted templates only with reviewer gates enabled.

---

## Metadata Schema (per use case)

Every registered use case must capture:

| Field | Type | Notes |
|---|---|---|
| `title` | string | Short, descriptive |
| `problem_statement` | text | What process problem it solves |
| `category` | enum | One of the 9 canonical categories above |
| `process_domain` | enum | P2P · O2C · Logistics · HR · Finance · IT · Other |
| `industry` | enum | Manufacturing · Retail · Financial Services · Healthcare · Public Sector · Other |
| `maturity` | enum | `concept` · `pilot` · `production` · `deprecated` |
| `api_dependencies` | list[str] | Celonis API names used |
| `outcome_metrics` | JSON | Measurable results (e.g. `{"cycle_time_reduction_pct": 18}`) |
| `client_id` | FK (optional) | Link to Client record; suppressed in public views |
| `project_id` | FK (optional) | Link to Project record; suppressed in public views |
| `owner_id` | FK | Person who owns the entry |
| `visibility` | enum | `internal` · `client` · `public` · `benchmark` |
| `status` | enum | `draft` · `submitted` · `approved` · `archived` |
| `tags` | list[str] | Free-form labels |
| `created_at` | datetime | Auto |
| `updated_at` | datetime | Auto |

---

## Phase Plan

### Phase 1 — Taxonomy & Governance  *(Weeks 1–2)*
> **Success metric:** 100% of current project use cases mapped to taxonomy categories.

| # | Initiative | Owner | Status | % | Blocker |
|---|---|---|---|---|---|
| 1.1 | Define and publish canonical taxonomy (9 categories) | Delivery Lead | ✅ Released | 100 | — |
| 1.2 | Define metadata schema and field-level redaction rules | Delivery Lead | ✅ Released | 100 | — |
| 1.3 | Define visibility matrix for 4 views | Delivery Lead | ✅ Released | 100 | — |
| 1.4 | Identify governance roles: content owner, reviewer, approver | Delivery Lead | 🔲 Planned | 0 | — |

---

### Phase 2 — Data Model & API Design  *(Weeks 3–6)*
> **Success metric:** All entities designed with documented contracts; zero breaking-change rework in Phase 3.

| # | Initiative | Owner | Status | % | Blocker |
|---|---|---|---|---|---|
| 2.1 | DB model: `UseCase`, `UseCaseTag`, `UseCaseLink`, `RoadmapInitiative` | Dev | 🟡 In Build | 50 | Tag/link refinement pending |
| 2.2 | Alembic migration | Dev | ✅ Released | 100 | — |
| 2.3 | Pydantic schemas: create · update · search · scoped output | Dev | ✅ Released | 100 | — |
| 2.4 | API routes: CRUD + search + scoped list endpoints | Dev | ✅ Released | 100 | — |
| 2.5 | Redaction service: field suppression by visibility mode | Dev | ✅ Released | 100 | — |
| 2.6 | Roadmap progress-tracking fields wired to `RoadmapInitiative` | Dev | ✅ Released | 100 | — |

---

### Phase 3 — Internal MVP  *(Weeks 7–10)*
> **Success metric:** Delivery team can fully search, filter, and manage use cases in the internal view.

| # | Initiative | Owner | Status | % | Blocker |
|---|---|---|---|---|---|
| 3.1 | Internal detailed UI page (search · facets · create / edit / archive) | Dev | 🔲 Planned | 0 | Phase 2 |
| 3.2 | Full-text + facet search (industry · domain · category · maturity) | Dev | 🔲 Planned | 0 | Phase 2 |
| 3.3 | Editorial workflow: submit → review → approve before external publish | Dev | 🔲 Planned | 0 | Phase 2 |
| 3.4 | Ingest 10 existing project patterns as seed entries | Delivery team | 🔲 Planned | 0 | 3.1 |

---

### Phase 4 — Multi-View Release  *(Weeks 11–16)*
> **Success metric:** All 4 views live; access-control tests pass for every view boundary.

| # | Initiative | Owner | Status | % | Blocker |
|---|---|---|---|---|---|
| 4.1 | Anonymized public view (identifier suppression) | Dev | 🔲 Planned | 0 | Phase 3 |
| 4.2 | Client-only portal view (client-scoped permissions) | Dev | 🔲 Planned | 0 | Phase 3 |
| 4.3 | Industry benchmark view (de-identified, aggregated rollups) | Dev | 🔲 Planned | 0 | Phase 3 |
| 4.4 | End-to-end access control test suite | QA | 🔲 Planned | 0 | 4.1–4.3 |

---

### Phase 5 — Scale & Adoption  *(Weeks 17–24)*
> **Success metric:** ≥ 80 % search success rate; monthly content cadence running.

| # | Initiative | Owner | Status | % | Blocker |
|---|---|---|---|---|---|
| 5.1 | Recommendation engine (suggest by project / industry / process domain) | Dev | 🔲 Planned | 0 | Phase 4 |
| 5.2 | Stale-entry detection and alerts (entries not updated in 90 days) | Dev | 🔲 Planned | 0 | Phase 4 |
| 5.3 | Contributor playbook and monthly review cadence | Delivery Lead | 🔲 Planned | 0 | Phase 4 |
| 5.4 | Quarterly taxonomy refresh process | Delivery Lead | 🔲 Planned | 0 | 5.3 |
| 5.5 | KPI dashboard: adoption rate · search success · publication lead time | Dev | 🔲 Planned | 0 | Phase 4 |

---

## Monthly Checkpoint Template

Copy and fill in at each monthly review:

```markdown
## Checkpoint — YYYY-MM

### Released this month
- …

### In build / discovery
- …

### Blocked / at risk
- Initiative ID:
- Blocker reason:
- Proposed resolution:

### KPI snapshot
| KPI | Target | Actual |
|---|---|---|
| Use cases in library | — | — |
| Search success rate | 80 % | — |
| Avg publication lead time | < 5 days | — |
| Views with live access control | 4 | — |

### Taxonomy drift check
- Categories added / removed:
- Reason:
```

---

## Out of Scope (V1)

- External partner marketplace publishing
- Automated ROI forecasting from outcome metrics
- Real-time Celonis tenant sync of use-case results

---

## Key Decisions

| Decision | Rationale | Date |
|---|---|---|
| Roadmap location: `docs/roadmap-use-cases.md` | Keeps docs in the established `docs/` layer | 2026-03-20 |
| 6-month horizon | Allows realistic phasing without over-committing | 2026-03-20 |
| 4 visibility modes in V1 | All four requested by delivery and account teams | 2026-03-20 |
| One success metric per phase | Prevents KPI sprawl; keeps reviews focused | 2026-03-20 |
| Single content owner for taxonomy | Prevents category drift across teams | 2026-03-20 |
