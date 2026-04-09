# Action-Flow Templates

This page explains how delivery teams use reusable action-flow templates in daily work.

## Where Templates Live

- Structured specs: `developer/action_flow_templates/specs/`
- Rollout playbooks: `developer/action_flow_templates/playbooks/`
- Template schema: `developer/action_flow_templates/schema/action-flow-template.schema.json`

## Daily Workflow

1. Select a template from the catalog.
2. Fill required client/project inputs.
3. Run sandbox validation with one expected failure path.
4. Collect evidence (logs, timeline links, reviewer decision).
5. Promote when governance checks pass.

## Risk Modes

- Low risk: notification/reporting templates.
- Medium risk: routing and recommendation templates.
- High risk: stopline and escalation templates with production impact.

## Good Practices

- Keep template customizations minimal and explicit.
- Prefer reusable mappings over hard-coded conditions.
- Review high-risk templates weekly until stable.
