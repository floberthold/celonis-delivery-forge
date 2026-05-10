# seed-forum-insights skill

This skill standardizes ingestion of forum discussion insights, converting community feedback into structured product roadmap signals.

## Quick start

```powershell
# Ingest forum insights from configured source
python scripts/seed_forum_insights.py --source forum-api

# Import from CSV export
python scripts/seed_forum_insights.py --import-csv forum-export.csv

# Refresh insights from all sources
python scripts/seed_forum_insights.py --refresh-all

# Dry run to preview what would be ingested
python scripts/seed_forum_insights.py --dry-run
```

## Artifacts

- Database: `foundry_db.sqlite` (ForumInsight model table)
- Raw imports: `.orchestration/forum-insights/raw/`
- Processed insights: `.orchestration/forum-insights/processed/`

## Insight Classification

- Feature requests
- Bug reports
- Integration questions
- Performance concerns
- Best practice discussions
- Blocker items
