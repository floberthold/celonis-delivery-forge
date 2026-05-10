---
name: debug-package-extraction
description: Provide diagnostics and debugging utilities for Celonis package extraction workflows and troubleshoot failures.
---

# Debug Package Extraction Skill

Use this skill when an agent needs to:

- Diagnose extraction failures for a specific package.
- Analyze extraction logs and performance bottlenecks.
- Validate field mappings and schema consistency.
- Check connection health and data source availability.
- Dry-run extractions without modifying state.
- Export detailed diagnostic reports.

## Tool usage order

1. Debug a package:
   - `python scripts/debug_package_extraction.py --package-id <id> --verbose`
2. Analyze extraction logs:
   - `python scripts/debug_package_extraction.py --analyze-logs --output report.html`
3. Dry run (no state changes):
   - `python scripts/debug_package_extraction.py --dry-run --package-id <id>`
4. Export diagnostics:
   - `python scripts/debug_package_extraction.py --export-diagnostics --format json`

## Expected outputs

- Debug report with detailed diagnostics.
- Field mapping validation results.
- Transformation pipeline inspection output.
- Error traces and recovery suggestions.
- Performance profiling data.

## Safety rules

- Do not modify extraction state in debug mode without explicit approval.
- Preserve sensitive credentials in diagnostic exports; redact as needed.
- Include full error context and stack traces for support escalation.
- Document transformation pipeline logic and expected outputs.
- Flag schema mismatches and version incompatibilities.
