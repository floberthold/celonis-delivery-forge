---
name: validate-action-flow-templates
description: Validate action flow template definitions against schema, ensuring workflow automation specs are correct and consistent.
---

# Validate Action Flow Templates Skill

Use this skill when an agent needs to:

- Validate workflow automation specs against JSON schema.
- Check required fields and structure consistency.
- Verify category, risk level, and error handling definitions.
- Generate updated template catalog from validated specs.
- Audit template compliance and best practices.

## Tool usage order

1. Validate all or specific templates:
   - All: `python scripts/validate_action_flow_templates.py --check-all`
   - Specific: `python scripts/validate_action_flow_templates.py <path>`
2. Regenerate catalog:
   - `python scripts/validate_action_flow_templates.py --catalog`
3. Strict mode (errors only):
   - `python scripts/validate_action_flow_templates.py --strict`

## Expected outputs

- Validation report (errors, warnings, passed specs).
- Updated `developer/action_flow_templates/catalog/template-catalog.json`.
- Spec file compliance audit.

## Safety rules

- Do not modify specs during validation; report violations only.
- Ensure schema version is declared in each spec.
- Require all required fields before approving specs.
- Preserve observability and error policy definitions.
- Document breaking changes when schema updates.
