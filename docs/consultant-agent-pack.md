# Consultant Support Agent Pack

Date started: 2026-03-22
Owner: Delivery Forge core team

## Purpose
This document defines practical supporting agents for day-to-day consultant work and how to execute them with governed run cards and isolated worktrees.

## Working Principle
- Keep agents focused on one consulting objective per run.
- Use explicit success criteria and stop conditions.
- Preserve evidence and decision trace for every client-facing output.
- Keep human review mandatory before external communication or production impact.

## Preset Agent Runs
The preset run generator supports these consultant workflows:

- Discovery: client discovery synthesis and opportunity shaping.
- WorkshopPrep: workshop planning, decision prompts, and agenda readiness.
- KPIDesign: KPI definition packs with assumptions and acceptance criteria.
- IssueTriage: backlog triage and owner-routed resolution plans.
- SteeringPack: steering committee status and decision package.
- RiskReview: risk and dependency review with mitigations and triggers.
- ClientComms: high-clarity client updates and escalation messages.
- FollowUp: meeting follow-up and action tracker generation.

## Command

```powershell
.\scripts\new_consultant_agent_run.ps1 -TaskId C-W13-001 -Preset Discovery -Owner "Delivery Forge core team" -Agent codex -BaseBranch main
```

## Typical Weekly Consultant Flow
1. Monday discovery and issue triage.
2. Midweek workshop prep and KPI design.
3. Thursday risk review and steering pack draft.
4. Friday client comms and follow-up action tracker.

## Governance Notes
- Assign a reviewer before run closure.
- Do not close run as DONE without evidence checklist completion.
- Use close_agent_run.ps1 for state transitions.
- Use list_agent_runs.ps1 -Summary -Json for weekly operational reporting.

## Suggested Starter Runs
- C-W13-001 Discovery
- C-W13-002 KPIDesign
- C-W13-003 SteeringPack
- C-W13-004 ClientComms

## Definition of Useful Support
An agent run is useful when it saves consultant time while improving consistency, traceability, and decision clarity.
