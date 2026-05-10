---
name: seed-forum-insights
description: Ingest forum discussion insights into the database, converting community feedback into structured product roadmap signals.
---

# Seed Forum Insights Skill

Use this skill when an agent needs to:

- Import new forum insights from configured sources or CSV exports.
- Classify discussions by type (feature requests, bugs, blockers, etc.).
- Refresh insights from all ingestion sources.
- Analyze community feedback patterns and themes.
- Dry-run imports to preview without committing.

## Tool usage order

1. Ingest from source:
   - From API: `python scripts/seed_forum_insights.py --source forum-api`
   - From CSV: `python scripts/seed_forum_insights.py --import-csv <file>`
2. Dry run to preview:
   - `python scripts/seed_forum_insights.py --dry-run`
3. Refresh all sources:
   - `python scripts/seed_forum_insights.py --refresh-all`

## Expected outputs

- Forum insight records in database (ForumInsight table).
- Raw imports stored in `.orchestration/forum-insights/raw/`.
- Processed and classified insights in `.orchestration/forum-insights/processed/`.

## Safety rules

- Preserve community member privacy and anonymity where appropriate.
- Accurately classify insight types (feature vs. bug vs. blocker).
- Include source URLs and discussion references.
- Document insight collection date and source system.
- Avoid misrepresenting feedback severity or frequency.
