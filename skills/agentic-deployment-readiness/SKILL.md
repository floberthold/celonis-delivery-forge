---
name: agentic-deployment-readiness
description: Check release gates and deployment readiness criteria for staging and production environments.
---

# Agentic Deployment Readiness Skill

Use this skill when an agent needs to:

- Verify deployment readiness gates before release.
- List pending approval criteria and blockers.
- Approve or gate specific deployment criteria.
- Track approval history and sign-offs.
- Validate quality metrics and compliance checks.

## Tool usage order

1. Check readiness for target environment:
   - `python -m foundry.mcp.agentic_deployment_readiness check --target production`
2. List pending gates:
   - `python -m foundry.mcp.agentic_deployment_readiness list-gates --target staging`
3. Approve or gate criteria:
   - `python -m foundry.mcp.agentic_deployment_readiness approve --gate <name> --target production`

## Expected outputs

- Gate status report (passed/pending/blocked).
- List of approval requirements.
- Deployment approval log entries.
- Blockers and their resolution status.

## Safety rules

- Do not bypass security or compliance gates.
- Require explicit approval sign-offs for production deployments.
- Preserve full approval audit trail.
- Validate test coverage thresholds before approval.
- Log all gate decisions with timestamp and approver identity.
