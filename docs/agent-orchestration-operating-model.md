# Agent Orchestration Operating Model

Date started: 2026-03-21
Owner: Delivery Forge core team

## Core Spirit
The shared spirit across modern orchestrators and Delivery Forge governance is:
- Parallel autonomy: run multiple scoped implementation streams at once.
- Isolation by default: each stream executes in its own git worktree and branch.
- Human-gated quality: no direct promotion without review evidence and policy checks.
- Visible flow: every run has a task card, status, owner, and outcome trace.
- Continuous looping with stop rules: autonomous loops are useful only with explicit exit criteria.

In short: autonomous where safe, governed where it matters.

## Delivery Forge Principles
- Two-hammer rule preserved: implementation can be automated, approval cannot.
- Evidence-first progression: status changes require objective artifacts.
- Small-batch execution: break work into reviewable, low-blast-radius slices.
- Reproducible operations: each run can be recreated from card + branch + logs.

## Minimal Operating Cycle
1. Create a run card and isolated worktree.
2. Execute agent implementation in that worktree.
3. Capture evidence (tests, screenshots, logs, diff summary).
4. Human review against governance checklist.
5. Merge or return to loop with explicit next task.

## Run States
- TODO: run defined, not started
- IN PROGRESS: active implementation in worktree
- IN REVIEW: evidence complete, awaiting human decision
- DONE: merged and validated
- BLOCKED: cannot continue due to dependency or decision

## Required Run Metadata
Each run must include:
- run_id
- task title and scope
- assigned agent/tooling
- base branch and run branch
- worktree path
- explicit success criteria
- explicit stop conditions
- evidence links
- final decision and rationale

## Quality Gates Before Merge
- Tests relevant to changed area pass.
- No unresolved security/compliance red flags.
- Reviewer confirms acceptance criteria were met.
- Evidence section is complete and reproducible.

## Commanded Implementation
Use the repository script to instantiate governed parallel runs:

```powershell
.\scripts\new_agent_run.ps1 -TaskId O6-PILOT-001 -Title "Parallel merge safety pilot" -Agent codex -Lane pilot -BaseBranch main
```

The script creates:
- Isolated git worktree in `.worktrees/`
- Run card in `.orchestration/runs/`
- Dedicated branch with deterministic naming

Close runs with gate enforcement:

```powershell
.\scripts\close_agent_run.ps1 -RunCard .\.orchestration\runs\O6-PILOT-001-o6-pilot-001-parallel-merge-safety-pilot.md -Status "IN REVIEW"
.\scripts\close_agent_run.ps1 -RunCard .\.orchestration\runs\O6-PILOT-001-o6-pilot-001-parallel-merge-safety-pilot.md -Status "DONE"
```

Enforced checks:
- `IN REVIEW` requires non-empty evidence fields (`Tests`, `Logs`, `Screenshots`, `Diff summary`).
- `DONE` requires prior `IN REVIEW`, complete evidence, and a review decision with `Reviewer` plus `Decision` (`approve` or `approved`).

List runs for daily triage:

```powershell
.\scripts\list_agent_runs.ps1
.\scripts\list_agent_runs.ps1 -Summary
.\scripts\list_agent_runs.ps1 -Summary -Json
.\scripts\list_agent_runs.ps1 -Status "IN REVIEW"
.\scripts\list_agent_runs.ps1 -Detailed
.\scripts\list_agent_runs.ps1 -Json
```

## First Rollout Policy
- Start with max 3 concurrent runs.
- Enforce one reviewer per run (not the author/operator).
- Enforce strict stop conditions for autonomous loops.
- Track cycle time, review latency, and defect escape rate weekly.

## Definition of Done for This Operating Model
- At least one pilot run completed through DONE with full evidence.
- At least one blocked scenario handled with explicit rationale.
- Team can repeat the cycle without ad-hoc process decisions.
