# update-forum-intake-log skill

This skill standardizes the weekly forum intake log process, tracking community feedback volume, themes, and blockers.

## Quick start

```powershell
# Add this week's forum intake log entry
python scripts/update_forum_intake_log.py `
  --week 2026-W13 `
  --reviewer "Delivery Forge team" `
  --search-terms "MLWB, integration, performance" `
  --threads-scanned 42 `
  --ideas-added 8 `
  --blockers "none"

# Auto-detect current week
python scripts/update_forum_intake_log.py `
  --reviewer "Your Name" `
  --search-terms "multi-level, governance, api" `
  --threads-scanned 35 `
  --ideas-added 12
```

## Artifacts

- `docs/roadmap-celonis.md` - Forum roadmap with weekly intake log table
- Log entries include: week, reviewer, search terms, scan volume, new ideas, blocking issues

## Log Attributes

- **Week**: ISO 8601 week number (YYYY-WNN)
- **Reviewer**: Name of person/team conducting intake
- **Search Terms**: Keywords used to identify relevant discussions
- **Threads Scanned**: Volume of forum discussions reviewed
- **Ideas Added**: Count of new roadmap items sourced
- **Blockers**: Notable customer-blocking issues identified
