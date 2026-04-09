# RTS Orchestration Roadmap

## Purpose
This roadmap defines the RTS-style orchestration layer for Celonis Delivery Forge.

It covers:
- symbolic world design for users, agents, clients, projects, assets, and tasks
- a quest system for targets and execution loops
- full user override controls so personal control always wins
- implementation phases and current status

## Last Updated
- Date: 2026-03-21
- Owner: Product / Engineering
- Status: Active

## Product Intent
Build a command-center experience where users orchestrate many agents across many clients, projects, and subtasks without losing governance, auditability, or personal control.

## Current Status Snapshot
| Track | Status | Notes |
|---|---|---|
| RTS concept and visual language | In Progress | Core mapping defined in this document |
| Quest system design | In Progress | Lifecycle and override rules defined |
| Data model extensions | Planned | Agent and quest entities not implemented yet |
| API and service orchestration | Planned | Requires model and migration phase first |
| UI world view vertical slice | Planned | Add route/template after API baseline |
| Telemetry and balancing | Planned | Start after vertical slice rollout |

## Symbolic Rendering System
Use symbolic metaphors that map directly to domain entities and status.

### World Objects
- Strongholds: organizations (tenant boundaries and team ownership)
- Regions: clients (delivery contexts)
- Districts: projects (execution zones)
- Sites: assets, reviews, and delivery files (work artifacts)
- Beacons: milestones and roadmap checkpoints

### Unit Types (Agents)
- Scouts: discovery and research agents (requirements, dependency mapping)
- Builders: implementation agents (code, docs, templates, workflows)
- Guardians: review and governance agents (quality, compliance, approvals)
- Couriers: integration and release agents (imports, exports, deployments)

### Status Effects and Signals
- Fog of war: unknown scope, low confidence, or missing data
- Supply lines: dependencies between tasks, projects, and integrations
- Threat markers: blockers, incidents, overdue items, review bottlenecks
- Control radius: confidence and readiness score around a team or feature area

## Quest System (Full User Control)
### Quest Types
- Main quests: strategic goals tied to roadmap phases and major delivery outcomes
- Side quests: optimization opportunities, refactors, cleanup, and quality upgrades
- Incident quests: urgent production, reliability, or governance interventions
- Guild quests: cross-project initiatives shared across teams

### Quest Sources
- User-authored quests (manual)
- Agent-suggested quests (derived from telemetry, backlog, and activity)
- Policy quests (generated from governance rules and deadlines)

### Lifecycle
`draft -> suggested -> accepted -> active -> blocked -> done -> archived`

### Personal Control Contract
- Users can create, edit, overwrite, pause, reprioritize, and delete any quest.
- User edits always take precedence over agent-generated content.
- Every agent suggestion must include provenance, rationale, and confidence.
- Users can freeze auto-generated quest updates for selected scopes.
- System stores user feedback for future suggestion quality but never auto-locks user decisions.

## Core Interface Blueprint
### Command Map
- World canvas shows organization, client, and project territories.
- Agent units move between territories based on assignments.
- Heat and alert overlays expose hotspots, blockers, and risk concentration.

### Command Panel
- Assign agents to quests and subtasks.
- Re-route priorities during incidents.
- Trigger safe actions and review gates.

### Quest Log
- Shows current objectives, deadlines, blockers, ownership, and confidence.
- Supports one-click user override actions and custom personal targets.

### Event Timeline
- Streams state changes, quest updates, review decisions, and integration outcomes.
- Links every event to entities and audit metadata.

## Planned Domain Extensions
### New Entities
- Agent
- AgentCapability
- Quest
- QuestObjective
- QuestAssignment
- QuestFeedback
- TaskDependency

### Service and API Additions
- agent registry and capability routing
- quest generation service with explanation payloads
- quest override endpoints for user control actions
- dependency graph endpoints for task blocking and unblocking
- orchestration timeline events for every quest and assignment transition

## Implementation Phases
### Phase A - Experience and Systems Blueprint
Status: In Progress

Deliverables:
- symbolic design system and mapping tables
- quest framework and control contract
- navigation and information architecture

### Phase B - Data Model and Migrations
Status: Planned

Deliverables:
- agent and quest tables
- dependency and feedback tables
- migration backfill and index strategy

### Phase C - Orchestration Services and API
Status: Planned

Deliverables:
- quest generation and override services
- assignment and dependency orchestration logic
- timeline event hooks and metrics counters

### Phase D - UI Vertical Slice
Status: Planned

Deliverables:
- new UI route and template for orchestration map
- quest log and command panel
- user override controls for all quest states

### Phase E - Simulation and Progression
Status: Planned

Deliverables:
- richer unit movement and territory updates
- escalation and auto-suggestion tuning
- personalization for play style and dashboard composition

### Phase F - Telemetry, Governance, and Balancing
Status: Planned

Deliverables:
- quest quality scoring and acceptance analytics
- override behavior analytics and recommendation tuning
- policy controls, alert thresholds, and operational runbooks

## Inspiration Inputs (Adapted, Not Copied)
- AI Town style signal: living world metaphor, ambient simulation, visible actor movement.
- Agent Forge style signal: modular role capability model and composable agent behavior.
- Paperclip style signal: tokenized visual language and strict mapping from design system to implementation.
- Additional references requested by user: Viberaft and Agentcraft-inspired collaborative command-center framing.

## Non-Goals for V1
- Real-time multiplayer world state.
- Fully autonomous irreversible agent actions.
- Replacing all existing CRUD pages on day one.

## Near-Term Backlog
1. Add agent and quest models with migration draft.
2. Add `/orchestration-ui` route and initial template shell.
3. Add quest CRUD plus override endpoints.
4. Add dependency graph service and blocked-state propagation.
5. Add command-map mock data adapter from existing project and todo entities.

## Risks and Mitigations
| Risk | Impact | Mitigation |
|---|---|---|
| Scope explosion from simulation ambitions | High | Keep V1 to command-center plus quest loop |
| Low trust in auto-generated quests | High | Make provenance, confidence, and override first-class |
| Data model complexity | Medium | Phase model rollout with minimal required fields |
| Visual complexity hurts usability | Medium | Keep map optional and pair with list-first quest log |

## Progress Log
- 2026-03-21: Created roadmap with symbolic rendering model, quest architecture, and phased plan.
- 2026-03-21: Locked full user-control policy for quest override behavior.