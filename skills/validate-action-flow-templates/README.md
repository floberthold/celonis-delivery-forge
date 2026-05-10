# validate-action-flow-templates skill

This skill validates action flow template definitions against the schema, ensuring consistency and correctness across all workflow automation specs.

## Quick start

```powershell
# Validate all action flow templates
python scripts/validate_action_flow_templates.py --check-all

# Validate a specific template
python scripts/validate_action_flow_templates.py developer/action_flow_templates/specs/my-workflow.json

# Generate catalog from validated templates
python scripts/validate_action_flow_templates.py --catalog

# Check for schema compliance only (no warnings)
python scripts/validate_action_flow_templates.py --strict
```

## Artifacts

- `developer/action_flow_templates/schema/` - JSON schema definitions
- `developer/action_flow_templates/specs/` - Validated template specs
- `developer/action_flow_templates/catalog/template-catalog.json` - Generated catalog

## Validation Checks

- Required fields (schema_version, template_id, title, steps, etc.)
- Category classification validity
- Risk level correctness
- Input/output schema consistency
- Error handling policy definitions
- Observability requirements
