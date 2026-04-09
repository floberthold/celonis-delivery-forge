# Template Authoring and Review Checklist

Use this checklist before adding or promoting an action-flow template.

## Author Checklist

- Template validates against `action-flow-template.schema.json`.
- Required inputs are minimal and clearly named.
- Idempotency key prevents duplicate side effects.
- Dead-letter path is explicit and actionable.
- Risk level is set correctly.
- Playbook includes setup, validation, and fallback sections.

## Reviewer Checklist

- Failure path behavior is tested and evidenced.
- Retry policy is bounded and appropriate.
- Owner and review cadence are defined.
- Timeline and logging signals are sufficient for audit.
- High-risk templates include rollback or manual containment.

## Promotion Rules

1. Medium/high risk templates require reviewer decision.
2. Missing fallback behavior blocks promotion.
3. Missing evidence bundle blocks promotion.

## Validation Command

Run this command before promotion:

```powershell
python scripts/validate_action_flow_templates.py
```
