# agentic-deployment-readiness skill

This skill standardizes deployment readiness checks, including release gates, approval criteria, and quality metrics.

## Quick start

```powershell
# Check deployment readiness for next release
python -m foundry.mcp.agentic_deployment_readiness check --target production

# List pending approval criteria
python -m foundry.mcp.agentic_deployment_readiness list-gates --target staging

# Approve or gate a deployment
python -m foundry.mcp.agentic_deployment_readiness approve --gate security-audit --target production
```

## Artifacts

- `.orchestration/deployment/` - Deployment readiness records
- `.orchestration/deployment/gates.json` - Release gate definitions and states
- `.orchestration/deployment/approval-log.jsonl` - Approval history

## Deployment Targets

- **staging**: Pre-production validation environment
- **production**: Live customer environment
- **canary**: Progressive rollout validation

## Gates Checked

- Test coverage thresholds
- Security scanning results
- Performance benchmarks
- Documentation completeness
- Approval sign-offs
