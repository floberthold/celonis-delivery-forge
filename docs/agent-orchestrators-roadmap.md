# Agent Orchestrators Adoption Roadmap

Date started: 2026-03-21
Owner: Delivery Forge core team
Source analyzed: https://github.com/andyrewlee/awesome-agent-orchestrators

## Purpose
This document captures idea discovery, evaluation plans, and adoption status for agent orchestrator tools relevant to Celonis Delivery Forge engineering workflows.

## Scope
- In scope: orchestration tools for coding agents, task routing, multi-worktree execution, and personal-assistant patterns with clear delivery-team value.
- Out of scope: direct implementation of external tools in this repository.

## Implemented Core Spirit Artifacts
- Operating model: `docs/agent-orchestration-operating-model.md`
- Run card template: `docs/templates/agent-run-card.md`
- Run bootstrap script: `scripts/new_agent_run.ps1`

These artifacts implement the common spirit as a repository-native workflow: isolated parallel runs, explicit status, evidence capture, and human-gated merge.

## Status Legend
- DONE: completed and validated
- IN PROGRESS: currently being implemented or evaluated
- IN REVIEW: pilot complete, pending decision
- TODO: planned, not started
- BLOCKED: waiting on dependency or decision

## Core Tracker: Selected Tools
All selected tools start as TODO.

| ID | Tool | Category | Core idea | Fit hypothesis for Delivery Forge | Key dependencies | Main risk | Owner | Target | Status |
|---|---|---|---|---|---|---|---|---|---|
| O1 | ai-maestro | Parallel Agent Runners | Dashboard for orchestrating Claude, Aider, Cursor across machines | Useful for cross-machine coordination during larger feature sprints | Secure remote session setup, consistent agent configs | Credential sprawl across machines | TBD | 2026-04-04 | TODO |
| O2 | CodexMonitor | Parallel Agent Runners | Orchestrate multiple Codex agents across local workspaces | High fit for local parallelization on backlog slices | Local workspace isolation, merge workflow discipline | Fragmented context across many parallel runs | TBD | 2026-04-04 | TODO |
| O3 | dorothy | Parallel Agent Runners | Desktop orchestration with automations, Kanban, MCP servers | Potential all-in-one operations cockpit for task flow | MCP server compatibility, desktop policy approval | Automation complexity can outpace team habits | TBD | 2026-04-08 | TODO |
| O4 | jean | Parallel Agent Runners | Desktop and web orchestration across projects and git worktrees | Strong fit for multi-project governance and review-ready branches | Worktree governance rules, auth and workspace policy | Operational overhead if project switching is noisy | Delivery Forge core team | 2026-03-28 | IN PROGRESS |
| O5 | openkanban | Parallel Agent Runners | TUI kanban board for orchestrating AI coding agents | Good lightweight option for terminal-first contributors | Terminal standards, board conventions | Limited visibility for non-terminal stakeholders | Delivery Forge core team | 2026-03-28 | IN PROGRESS |
| O6 | parallel-code | Parallel Agent Runners | Desktop orchestration with isolated worktrees, diff viewer, one-click merge | Strong candidate for safe parallel execution and fast review | Worktree automation, merge policy controls | One-click merge misuse without guardrails | Delivery Forge core team | 2026-03-28 | IN PROGRESS |
| O7 | symphony | Parallel Agent Runners | Isolated autonomous implementation runs | High value for repeatable implementation batches | Task decomposition quality, autonomous run governance | Hidden regressions if verification is weak | TBD | 2026-04-15 | TODO |
| O8 | vibecraft | Parallel Agent Runners | RTS-style workspace for managing coding agents | Could improve planning and operator awareness in complex streams | Team training, interface adoption | Novel UX may reduce adoption speed | TBD | 2026-04-15 | TODO |
| O9 | accomplish | Personal Assistants | Desktop AI coworker for ongoing workflows | Useful for personal productivity and repetitive coordination tasks | Local policy approvals, privacy checks | Scope creep into non-engineering workflows | TBD | 2026-04-17 | TODO |
| O10 | assistant | Personal Assistants | Panel-based personal assistant with plugin architecture | Good plugin-based experiment for focused internal productivity tools | Plugin review process, extension security model | Plugin quality and maintenance burden | TBD | 2026-04-17 | TODO |
| O11 | paperclip | Multi-Agent Swarms | Orchestration for zero-human companies | Strategic exploration for long-horizon automation posture | Governance model, compliance sign-off | Misalignment with required human-in-the-loop controls | TBD | 2026-04-22 | TODO |
| O12 | ralph-tui | Autonomous Loop Runners | Orchestrate coding agents through task lists autonomously | High fit for backlog burn-down loops with explicit tasks | Reliable task definitions, stop conditions | Over-running loops without strict exit criteria | TBD | 2026-04-22 | TODO |

## Phase Plan

### Phase 1: Discovery and Scoring (Weeks 1-2)
Status: IN PROGRESS

Goals:
- Build a repeatable scoring rubric for orchestration-tool fit.
- Evaluate installation viability, platform support, and governance model.
- Establish minimum security and compliance requirements.

Deliverables:
- Scoring template with weighted criteria.
- Initial scorecards for O1-O12.
- Risk log with go/no-go flags.
- Operating model and run-card workflow scaffold.

Exit criteria:
- Every selected tool has a scorecard and recommendation.
- Security baseline risks documented for each tool.

#### Phase 1 Scorecards (Initial Baseline)
Scoring scale: 1 (low) to 5 (high).

Weighted criteria:
- Workflow fit (30 percent): alignment to Delivery Forge day-to-day engineering flow.
- Integration effort (20 percent): estimated setup and operational complexity.
- Governance readiness (20 percent): security, auditability, and policy control potential.
- Collaboration value (15 percent): team visibility, coordination, and handoff quality.
- Maturity signals (15 percent): project activity and practical operational confidence.

Recommendation bands:
- 4.0 to 5.0: shortlist for Phase 2 pilot
- 3.0 to 3.9: monitor and optionally pilot
- below 3.0: defer unless strategic requirement emerges

| ID | Tool | Workflow fit (30%) | Integration effort (20%) | Governance readiness (20%) | Collaboration value (15%) | Maturity signals (15%) | Weighted score | Phase 1 recommendation |
|---|---|---:|---:|---:|---:|---:|---:|---|
| O1 | ai-maestro | 3.5 | 2.5 | 2.5 | 3.5 | 3.0 | 3.05 | Monitor and optionally pilot |
| O2 | CodexMonitor | 4.0 | 4.0 | 3.0 | 3.5 | 3.0 | 3.55 | Monitor and optionally pilot |
| O3 | dorothy | 4.0 | 3.0 | 3.0 | 4.5 | 3.0 | 3.60 | Monitor and optionally pilot |
| O4 | jean | 4.5 | 3.0 | 3.5 | 4.5 | 3.0 | 3.80 | Monitor and optionally pilot |
| O5 | openkanban | 3.5 | 4.5 | 3.0 | 3.5 | 3.5 | 3.65 | Monitor and optionally pilot |
| O6 | parallel-code | 4.5 | 3.5 | 3.5 | 4.0 | 3.5 | 3.95 | Monitor and optionally pilot |
| O7 | symphony | 4.5 | 3.0 | 3.0 | 3.5 | 3.0 | 3.55 | Monitor and optionally pilot |
| O8 | vibecraft | 3.5 | 3.0 | 2.5 | 4.0 | 2.5 | 3.15 | Monitor and optionally pilot |
| O9 | accomplish | 2.5 | 3.0 | 2.5 | 2.5 | 3.0 | 2.70 | Defer unless strategic requirement emerges |
| O10 | assistant | 2.5 | 3.0 | 3.0 | 3.0 | 3.0 | 2.85 | Defer unless strategic requirement emerges |
| O11 | paperclip | 2.0 | 2.0 | 1.5 | 2.5 | 2.5 | 2.10 | Defer unless strategic requirement emerges |
| O12 | ralph-tui | 4.0 | 4.0 | 3.0 | 3.5 | 3.0 | 3.55 | Monitor and optionally pilot |

Initial pilot shortlist candidates (highest score and fit):
- O6 parallel-code
- O4 jean
- O5 openkanban

### Phase 2: Pilot Fit Checks (Weeks 3-4)
Status: TODO

Pilot runs bootstrapped:
- `O6-PILOT-001-o6-pilot-001-parallel-code-pilot-for-safe-merge-acceleration`
- `O4-PILOT-001-o4-pilot-001-jean-pilot-for-multi-project-worktree-orchestration`
- `O5-PILOT-001-o5-pilot-001-openkanban-pilot-for-terminal-first-agent-flow`

Goals:
- Pilot top candidates in isolated sandboxes.
- Validate compatibility with git worktree workflows.
- Measure cycle-time improvement versus baseline.

Deliverables:
- Pilot runbooks and setup notes.
- Baseline versus pilot metrics (lead time, review latency, merge quality).
- Decision memo on shortlist for controlled rollout.

Exit criteria:
- At least 3 shortlisted tools complete pilot scenarios.
- No critical blocker remains unresolved for shortlisted tools.

### Phase 3: Controlled Rollout (Weeks 5-6)
Status: TODO

Goals:
- Introduce approved tools to a limited engineering cohort.
- Standardize workflow guardrails and review practices.
- Add observability for agent-run quality and outcomes.

Deliverables:
- Team onboarding guide and operating constraints.
- Rollout checklists for worktree safety and merge verification.
- Dashboard or report template for weekly adoption metrics.

Exit criteria:
- Pilot cohort reaches target usage and quality thresholds.
- Merge and regression rates remain within acceptable bounds.

### Phase 4: Operationalization (Weeks 7-8)
Status: TODO

Goals:
- Turn validated practices into default operating playbooks.
- Add maintenance ownership and update cadence.
- Define deprecation path for low-value tools.

Deliverables:
- Long-term support model and ownership matrix.
- Quarterly review checklist.
- Sunset criteria for low-fit tools.

Exit criteria:
- One or more tools adopted with clear owner and runbook.
- Backlog continuously triaged with status evidence.

## Per-Tool Plans

### O1 ai-maestro
- Why it is interesting: Multi-machine orchestration can unlock larger parallel implementation windows.
- Evaluation tasks:
  - Verify onboarding on Windows developer machines.
  - Test coordination between at least two machine contexts.
  - Validate credential and secret handling model.
- PoC success criteria: 2 parallel tasks completed with auditable outputs and no credential leakage.
- Integration notes: Favor project-level config templates and explicit machine ownership tagging.
- Status: TODO

### O2 CodexMonitor
- Why it is interesting: Directly aligned with Codex-heavy local workflows.
- Evaluation tasks:
  - Run three concurrent local workspace tasks.
  - Validate conflict handling and reconciliation flow.
  - Measure review throughput impact.
- PoC success criteria: 20 percent faster parallel delivery on a controlled task set.
- Integration notes: Require branch naming standards and merge checkpoints.
- Status: TODO

### O3 dorothy
- Why it is interesting: Combines orchestration, automation, Kanban, and MCP in one desktop workflow.
- Evaluation tasks:
  - Validate MCP server interoperability with existing tooling.
  - Test automation recipes for recurring engineering actions.
  - Confirm Kanban-state transitions map to team process.
- PoC success criteria: One sprint lane managed end-to-end without process drift.
- Integration notes: Start with read-only automations before enabling write actions.
- Status: TODO

### O4 jean
- Why it is interesting: Multi-project and worktree-native operation could support broader portfolio execution.
- Evaluation tasks:
  - Test project switching and context persistence.
  - Validate worktree lifecycle operations against team conventions.
  - Evaluate collaboration ergonomics between desktop and web modes.
- PoC success criteria: Stable cross-project orchestration for one feature stream.
- Integration notes: Enforce standardized worktree naming and cleanup policy.
- Status: IN PROGRESS

### O5 openkanban
- Why it is interesting: Lightweight TUI control plane for agent tasks.
- Evaluation tasks:
  - Map current backlog taxonomy to openkanban columns.
  - Test handoff clarity between human owners and agent runs.
  - Validate terminal UX for daily operation.
- PoC success criteria: Team can complete weekly planning and execution within TUI flow.
- Integration notes: Pair with markdown export for stakeholder visibility.
- Status: IN PROGRESS

### O6 parallel-code
- Why it is interesting: Isolated worktrees plus diff viewer and one-click merge can accelerate safe parallel work.
- Evaluation tasks:
  - Run parallel coding sessions across at least four tasks.
  - Validate one-click merge against policy checks.
  - Measure review effort with built-in diff viewer.
- PoC success criteria: Faster merges with no increase in post-merge defects.
- Integration notes: Require pre-merge tests and protected branch rules.
- Status: IN PROGRESS

### O7 symphony
- Why it is interesting: Autonomous isolated runs align with structured implementation batches.
- Evaluation tasks:
  - Define task contracts for autonomous runs.
  - Validate run traceability and artifact capture.
  - Test stop and rollback controls.
- PoC success criteria: Autonomous run completes scoped task with review-ready artifacts.
- Integration notes: Add mandatory validation stage between run completion and merge.
- Status: TODO

### O8 vibecraft
- Why it is interesting: Visual RTS-style coordination may improve operator awareness for parallel streams.
- Evaluation tasks:
  - Compare decision speed versus list-based orchestration.
  - Validate complexity handling for 5-plus concurrent tasks.
  - Assess learning curve for contributors.
- PoC success criteria: Improved coordination metrics without productivity regression.
- Integration notes: Pilot with a small operator group first.
- Status: TODO

### O9 accomplish
- Why it is interesting: Personal desktop coworker model can reduce coordination overhead.
- Evaluation tasks:
  - Identify top 3 repetitive workflows to automate.
  - Validate local-data privacy posture.
  - Test reliability across multi-day usage.
- PoC success criteria: Measurable reduction in repetitive manual task time.
- Integration notes: Keep usage scoped to non-sensitive coordination tasks.
- Status: TODO

### O10 assistant
- Why it is interesting: Plugin architecture enables targeted productivity enhancements.
- Evaluation tasks:
  - Evaluate plugin security and permission boundaries.
  - Build one low-risk internal plugin prototype.
  - Validate maintainability burden for plugin lifecycle.
- PoC success criteria: Prototype plugin saves time without raising support load.
- Integration notes: Define plugin acceptance criteria before expansion.
- Status: TODO

### O11 paperclip
- Why it is interesting: Long-range strategic idea for deeply autonomous operations.
- Evaluation tasks:
  - Assess compatibility with human-governed engineering controls.
  - Model organizational and compliance implications.
  - Identify bounded use cases where autonomy is acceptable.
- PoC success criteria: Clear decision on whether to pursue narrow pilot.
- Integration notes: Require explicit human approval gates by design.
- Status: TODO

### O12 ralph-tui
- Why it is interesting: Autonomous loop runner fits backlog-driven execution.
- Evaluation tasks:
  - Test loop execution against a curated task list.
  - Validate stop conditions and escalation paths.
  - Measure completion quality across loop iterations.
- PoC success criteria: Reliable autonomous progress with controlled loop exits.
- Integration notes: Introduce strict task templates and max-iteration limits.
- Status: TODO

## Cross-Cutting Decision Framework
- Security and compliance gates:
  - No unmanaged secret propagation.
  - Explicit access-control model documented before pilot.
  - Auditability of agent actions required.
- Licensing and legal:
  - Verify repository license compatibility and dependencies.
  - Record restrictions for commercial/internal use.
- Observability requirements:
  - Capture run metadata, task outcomes, and failure reasons.
  - Preserve traceability from task assignment to merged change.
- Cost model:
  - Estimate runtime/tooling overhead versus cycle-time improvements.
  - Track pilot cost per completed task.
- Team workflow impact:
  - Measure onboarding effort and operational complexity.
  - Document role changes for operators, reviewers, and maintainers.

## Weekly Tracking Template
Use this table to track implementation cadence.

| Week | Focus | Planned | Done | Risks | Decision Needed |
|---|---|---|---|---|---|
| 2026-W12 | Roadmap setup | O1-O12 scope, rubric draft | Roadmap created | Tool landscape churn | Finalize scoring weights |
| 2026-W13 | Discovery | Scorecards for O1-O6 | Scorecards completed; O4/O5/O6 pilots bootstrapped with active run cards, worktrees, pre-assigned reviewers, and evidence deadline set to 2026-03-25 (owner: Delivery Forge core team) | Baseline metrics still need capture | Confirm baseline metric extraction method for cycle time and review latency |
| 2026-W14 | Discovery | Scorecards for O7-O12 |  |  |  |
| 2026-W15 | Pilot | Pilot shortlist execution |  |  |  |
| 2026-W16 | Rollout decision | Adoption memo and controls |  |  |  |

## Status Transition Rules
- Move TODO to IN PROGRESS only when an owner and explicit evaluation task list are assigned.
- Move IN PROGRESS to IN REVIEW only with PoC evidence and risk notes.
- Move IN REVIEW to DONE only after approval by roadmap owner and documented operating guardrails.
- Move to BLOCKED immediately when a dependency prevents meaningful progress.

## Evidence Requirements
Status updates must include:
- Date of change
- Owner
- What was evaluated or delivered
- Objective evidence (notes, metrics, screenshots, or logs)
- Next action

## Appendix: Additional Awesome List Candidates
This appendix tracks broader candidates outside the 12 selected tools. Start all items as TODO until triaged.

### Parallel Agent Runners (Backlog)
| Tool | Short note | Triage status |
|---|---|---|
| 1code | UI approach for local and remote execution | TODO |
| agent-deck | Terminal session manager model | TODO |
| agent-orchestrator | Parallel coding orchestrator baseline | TODO |
| aizen | macOS worktree workspace focus | TODO |
| amux | TUI parallel runner simplicity | TODO |
| Aperant | Autonomous multi-session coding | TODO |
| ariana | Agentic IDE direction | TODO |
| automaker | Autonomous AI dev studio model | TODO |
| claude-squad | Background multi-agent management | TODO |
| claude_code_bridge | Real-time multi-AI collaboration | TODO |
| cmux | Open platform for parallel agent runs | TODO |
| constellagent | Isolated terminal editor worktree setup | TODO |
| crystal | Parallel Codex and Claude sessions | TODO |
| dmux | tmux plus worktree orchestration | TODO |
| emdash | Parallel coding agent runner | TODO |
| ghast | Multi-terminal multitasking pattern | TODO |
| humanlayer | Human-in-the-loop for hard codebases | TODO |
| jat | Agentic IDE product direction | TODO |
| lalph | Issue-driven orchestration style | TODO |
| mux | Desktop isolated agentic development | TODO |
| subtask | Worktree subagent skill pattern | TODO |
| supacode | Native macOS orchestrator approach | TODO |
| superset | Terminal for coding agents | TODO |
| t3code | Minimal web GUI for coding agents | TODO |
| vibe-kanban | Kanban board for agent management | TODO |
| vibe-tree | Parallel git worktree vibe coding | TODO |

### Personal Assistants (Backlog)
| Tool | Short note | Triage status |
|---|---|---|
| babyagi3 | Config-once assistant pattern | TODO |
| cashclaw | Autonomous paid-work loop concept | TODO |
| ClawWork | OpenClaw coworker ecosystem | TODO |
| CoPaw | Personal AI assistant baseline | TODO |
| denchclaw | Managed CRM/sales automation focus | TODO |
| ghostclaw | Computer-resident assistant model | TODO |
| hermes-agent | Long-lived personal agent concept | TODO |
| ironclaw | Rust privacy/security focus | TODO |
| lemon | Local-first assistant system | TODO |
| leon | Voice and text open assistant | TODO |
| lettabot | Memory-centric assistant pattern | TODO |
| lobsterai | Always-on work assistant model | TODO |
| mercury | Chat-native assistant behavior | TODO |
| MetaClaw | Learning/evolving assistant concept | TODO |
| nanobot | Ultra-lightweight assistant path | TODO |
| nanoclaw | Containerized lightweight assistant | TODO |
| NemoClaw | Secure OpenClaw installation plugin | TODO |
| nullclaw | Autonomous assistant infrastructure | TODO |
| openclaw | Personal assistant platform baseline | TODO |
| piclaw | Pi-based assistant deployment | TODO |
| picoclaw | Ultra-efficient assistant variant | TODO |
| rho | Persistent, proactive assistant model | TODO |
| rowboat | Coworker plus memory emphasis | TODO |
| takopi | Messaging bridge to coding agents | TODO |
| zclaw | Embedded minimal assistant concept | TODO |
| zeroclaw | Autonomous assistant infrastructure | TODO |

### Multi-Agent Swarms (Backlog)
| Tool | Short note | Triage status |
|---|---|---|
| antfarm | One-command team creation | TODO |
| automata | Agent swarming organization system | TODO |
| claude-flow | Coordinated swarm workflows | TODO |
| ClawTeam | Command-driven full automation swarm | TODO |
| clawe | Trello-like coordination for agents | TODO |
| CompanyHelm | Distributed orchestrator with conversations | TODO |
| gastown | Persistent multi-agent work tracking | TODO |
| kodo | Multi-agent coding cycles with verification | TODO |
| loom | Evolutionary autonomous loops | TODO |
| openfang | Agent operating system approach | TODO |
| opengoat | Autonomous organization builder | TODO |
| ORCH | Typed agent teams with state machine | TODO |

### Autonomous Loop Runners (Backlog)
| Tool | Short note | Triage status |
|---|---|---|
| ralph-claude-code | Looping Claude with exit detection | TODO |
| ralph-orchestrator | Hat-based loop orchestration | TODO |
| ralphy | Task loop until done | TODO |
| wreckit | Roadmap-driven Ralph loop | TODO |

## Last Reviewed
- Date: 2026-03-21
- Reviewer: GitHub Copilot (GPT-5.3-Codex)
- Basis: awesome-agent-orchestrators README snapshot and internal roadmap conventions
