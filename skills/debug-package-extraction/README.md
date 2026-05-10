# debug-package-extraction skill

This skill provides diagnostics and debugging utilities for Celonis package extraction workflows, helping identify and troubleshoot extraction failures.

## Quick start

```powershell
# Debug extraction for a specific package
python scripts/debug_package_extraction.py --package-id "pkg-12345" --verbose

# Analyze extraction logs
python scripts/debug_package_extraction.py --analyze-logs --output debug-report.html

# Dry run extraction to test without modifying state
python scripts/debug_package_extraction.py --dry-run --package-id "pkg-12345"

# Export extraction diagnostics
python scripts/debug_package_extraction.py --export-diagnostics --format json
```

## Artifacts

- `.orchestration/extractions/debug/` - Debug logs and diagnostics
- `.orchestration/extractions/debug/latest-report.json` - Most recent debug report
- `.orchestration/extractions/debug/traces/` - Full extraction traces

## Diagnostics Provided

- Field mapping validation
- Connection health checks
- Transformation pipeline inspection
- Schema mismatch detection
- Performance bottleneck analysis
- Error stack traces and recovery suggestions
