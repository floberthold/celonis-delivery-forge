# Celonis Delivery Forge Master Roadmap

## Purpose
This is the top-level roadmap for Celonis Delivery Forge.

It exists to collect in one place:
- the product direction
- the current ideas backlog
- the phased implementation plan
- the current progress snapshot
- links to the more detailed sub-roadmaps

Use this file as the starting point. Use the linked roadmap files for feature-area detail.

## Last Updated
- Date: 2026-03-21
- Owner: Product / Engineering
- Status: Active

## Product Direction
Celonis Delivery Forge is moving from a local delivery-governance tool toward a multi-tenant software service for consultants, freelancers, and teams.

The target model is:
- individual users have their own workspace, preferences, and personal agent support
- organizations provide the shared tenant, billing boundary, and collaboration space
- clients, projects, assets, reviews, templates, and shared agents live inside the organization context
- AI agents support both reasoning and automation at personal, shared, and project scope

## Guiding Product Idea
Build a delivery operating system for Celonis work:
- personal "IDE" experience per user
- shared team workspace per organization
- governance and auditability built in
- reusable methodology, templates, and playbooks
- agent-assisted execution on top of the delivery data model

## Current State Snapshot
### Already present in the product
- project, client, asset, review, timeline, todo, template, and Celonis integration foundations
- JWT-based local authentication
- desktop/local-first runtime mode
- UI dashboard and topic pages
- multiple focused roadmap documents in `docs/`

### Recently implemented foundation work
- organization entity added
- organization membership entity added
- org-aware login flow added
- current-actor dependency added to resolve active organization context
- `/orgs` routes added for create, mine, and active organization access
- organization migration added
- core shared entities now carry `organization_id` for SaaS tenant scoping
- client, project, asset, todo, template, Celonis connection, and timeline API routes now require an active org and filter by it
- activity logging is now org-aware for scoped API operations
- newly created organizations are seeded with their own default template library
- first UI tenant-scoping slice landed for dashboard, client health, projects UI, and assets UI
- second UI tenant-scoping slice landed for reviews, clients, todos, templates, and timeline core flows
- third UI tenant-scoping slice landed for people/client/project overviews and GitLab overview/actions
- fourth UI tenant-scoping slice landed for files UI, KPI UI, and snapshot UI access paths
- fifth UI tenant-scoping slice landed for organization-aware people management and person membership lifecycle
- sixth tenant-scoping slice landed in backend APIs for KPI, KPI-book, and snapshots routes
- seventh tenant-scoping slice landed in backend APIs for files and GitLab routes
- eighth tenant-scoping slice landed in backend APIs for users/people, use-cases, and ingest routes

### Not done yet
- full tenant isolation across every remaining domain entity and UI flow
- personal workspace model
- agent model and orchestration layer
- subscriptions, billing, and usage metering

## Progress Summary
| Area | Status | Notes |
|---|---|---|
| Core delivery workflow | In Progress | Existing base app is operational and expanding |
| Celonis integration maturity | In Progress | Basic connectivity and actions exist |
| Use-case library | In Progress | Model and roadmap work are underway |
| Forum insight tracking | In Progress | Data model and routes are being added |
| SaaS multi-tenancy foundation | In Progress | Organization/auth groundwork and first core API scoping are in place |
| Personal workspace | Planned | Depends on stronger org scoping |
| Agent platform | Planned | Vision defined, implementation not started |
| RTS orchestration UX | In Progress | Dedicated roadmap and quest-control model are defined |
| Billing / subscriptions | Planned | Not started |

## Master Phase Plan
### Phase 0 — Multi-Tenant Foundation
Status: In Progress

Goal:
- establish organizations as the tenant boundary
- make authentication aware of active organization context
- prepare the data model for tenant isolation

Scope:
- organization and organization membership models
- org-aware token issuance and dependency resolution
- base org routes
- first-pass `organization_id` scoping across core shared entities
- org-aware template seeding and activity logging
- next: extend scoping to the remaining entities, UI flows, and safe backfill/constraint tightening

### Phase 1 — Platform Stability and Workflow Hardening
Status: In Progress

Goal:
- stabilize auth, migrations, route behavior, and workflow correctness

Scope:
- migration consistency
- stronger service validations
- better activity logging coverage
- improved todo/review/project lifecycle handling

### Phase 2 — Celonis Delivery Depth
Status: In Progress

Goal:
- move from raw endpoint calls to guided delivery operations around Celonis work

Scope:
- diagnostics and connection maturity
- stronger Celonis object workflows
- better visibility for integration failures and health

### Phase 3 — Use-Case and Knowledge Layer
Status: In Progress

Goal:
- turn project knowledge into a structured, reusable asset library

Scope:
- use-case library
- taxonomy and visibility model
- roadmap items and knowledge retrieval support

### Phase 4 — Personal Workspace
Status: Planned

Goal:
- give each user a personal operating space inside the shared organization

Scope:
- user preferences
- dashboard layout and widgets
- personal task/review/activity views
- personal drafts and saved views

### Phase 5 — Agent Platform
Status: Planned

Goal:
- add personal, org, and project scoped agents that can reason over the system and execute safe actions

Scope:
- agent registry
- agent conversations and memory
- tool calling into internal APIs
- scheduled and event-driven automations
- shared specialist agents and orchestration pattern

### Phase 6 — SaaS Commercialization
Status: Planned

Goal:
- make the platform purchasable and operable as a real service

Scope:
- subscription model
- seat management
- onboarding and org invites
- usage metering
- billing integration

## Current Priority Queue
1. Finish tenant foundation across the remaining domain entities and UI flows.
2. Keep the Alembic migration chain clean and deterministic.
3. Add safe backfill and later non-null enforcement for `organization_id` where appropriate.
4. Harden workflow correctness in review, todo, and project transitions.
5. Start the personal workspace model once org scoping is reliable.
6. Start the agent platform after the personal/shared boundary is explicit in data and permissions.

## Key Open Decisions
1. Should personal identity remain global across all organizations, with org membership handling context switching?
2. Which entities must become org-scoped first: client, project, asset, template library, todo, activity log?
3. What is the first useful agent: review copilot, project brief generator, timeline summarizer, or methodology assistant?
4. How should methodology be modeled: templates only, or first-class playbooks with agent prompts and review rules?
5. Should billing be seat-based, usage-based, or hybrid?

## Linked Roadmaps
Use these for detailed planning within each area:

- `docs/dev-roadmap.md` — engineering execution roadmap
- `docs/agent-feature-roadmap.md` — Celonis capability coverage and agent-facing implementation status
- `docs/roadmap-celonis.md` — Celonis-informed platform roadmap
- `docs/roadmap-use-cases.md` — use-case library roadmap
- `docs/celonis-assets-roadmap.md` — asset-related roadmap
- `docs/celonis-forum-insights-roadmap.md` — forum insight roadmap
- `docs/celonis-mcp-roadmap.md` — MCP-related roadmap
- `docs/rts-orchestration-roadmap.md` — RTS interface, quest system, and orchestration rollout plan
- `docs/domain-submodule-local-first-replatform.md` — domain-sliced local-first rollout model and activation profiles

## Update Rules
- Update this file whenever the overall direction, phase ordering, or cross-cutting priorities change.
- Update this file when a major phase changes state.
- Keep detailed acceptance criteria and feature checklists in the linked sub-roadmaps.
- If a new focused roadmap is created, add it to the Linked Roadmaps section.

## Change Log
- 2026-03-21: Created master roadmap to consolidate ideas, plan, progress, and sub-roadmap links.
- 2026-03-21: Recorded SaaS + personal workspace + agent-platform direction.
- 2026-03-21: Recorded Phase 0 organization/auth foundation as in progress.
- 2026-03-21: Recorded first tenant-scoped API slice across clients, projects, assets, templates, todos, Celonis connections, and timeline.
- 2026-03-21: Recorded first tenant-scoped UI slice across dashboard, client health, projects UI, and assets UI.
- 2026-03-21: Recorded second tenant-scoped UI slice across reviews, clients, todos, templates, and timeline core flows.
- 2026-03-21: Recorded third tenant-scoped UI slice across people/client/project overviews plus GitLab overview/actions.
- 2026-03-21: Recorded fourth tenant-scoped UI slice across files UI, KPI UI, and snapshot UI access paths.
- 2026-03-21: Recorded fifth tenant-scoped UI slice across people management and org membership-aware person create/remove flows.
- 2026-03-21: Recorded backend tenant-scoping updates for KPI, KPI-book, and snapshot API route ownership checks.
- 2026-03-21: Recorded backend tenant-scoping updates for files and GitLab API route ownership checks.
- 2026-03-21: Recorded backend tenant-scoping updates for users/people, use-cases, and ingest API route ownership checks.
- 2026-03-21: Added RTS orchestration roadmap and quest full-control direction to linked plans.