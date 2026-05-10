---
name: update-forum-intake-log
description: Standardize weekly forum intake logging process, tracking community feedback volume, themes, and blockers.
---

# Update Forum Intake Log Skill

Use this skill when an agent needs to:

- Record weekly forum intake summary.
- Track community feedback volume and themes.
- Identify blocking issues and critical concerns.
- Maintain searchable intake history.
- Generate intake trends and patterns.

## Tool usage order

1. Add intake log entry:
   ```powershell
   python scripts/update_forum_intake_log.py \
     --week 2026-W13 \
     --reviewer "Name" \
     --search-terms "keywords" \
     --threads-scanned <n> \
     --ideas-added <n>
   ```
2. Auto-detect current week:
   - Week parameter defaults to current ISO week if omitted.
3. Review updated log in `docs/roadmap-celonis.md`.

## Expected outputs

- Updated intake log entry in `docs/roadmap-celonis.md`.
- Week, reviewer, search terms, thread count, ideas count, blockers.
- Append-only history with no overwrites.

## Safety rules

- Preserve existing intake log entries; only append.
- Use consistent reviewer names for tracking continuity.
- Document blocking issues explicitly and thoroughly.
- Normalize special characters in cell values (| → /).
- Include representative search terms for reproducibility.
