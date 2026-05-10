---
name: seed-use-cases
description: Seed and update use case definitions in the database with consistent metadata and classifications.
---

# Seed Use Cases Skill

Use this skill when an agent needs to:

- Initialize use case definitions from seed data.
- Update use case attributes (maturity, classifications, dependencies).
- Verify use case metadata consistency.
- Track use case lifecycle (draft → validated → production).
- Manage API dependency declarations.

## Tool usage order

1. Seed use cases:
   - All: `python scripts/seed_use_cases.py --mode all`
   - Category: `python scripts/seed_use_cases.py --mode category --category <name>`
2. Dry run to preview:
   - `python scripts/seed_use_cases.py --dry-run`
3. Update attributes:
   - `python scripts/seed_use_cases.py --update-maturity`

## Expected outputs

- Use case records in `foundry_db.sqlite` (UseCase table).
- Seed manifest applied to database.
- Maturity level updates and classifications.

## Safety rules

- Preserve existing use case IDs and historical data.
- Only update intended fields; do not blanket-overwrite.
- Validate required fields before committing to database.
- Document use case dependencies and API requirements.
- Maintain consistent industry and domain classifications.
