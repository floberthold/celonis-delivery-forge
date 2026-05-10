# seed-use-cases skill

This skill standardizes seeding and updating use case definitions in the database, ensuring consistent metadata and classifications.

## Quick start

```powershell
# Seed all default use cases
python scripts/seed_use_cases.py --mode all

# Seed specific use case category
python scripts/seed_use_cases.py --mode category --category "3p-enrichment"

# Dry run to see what would be seeded
python scripts/seed_use_cases.py --dry-run

# Update existing use case maturity levels
python scripts/seed_use_cases.py --update-maturity
```

## Artifacts

- Database: `foundry_db.sqlite` (UseCase model table)
- Seed manifest: Defined in script SEED_USE_CASES variable

## Use Case Attributes

- Title and summary
- Problem statement
- Industry classification
- Process domain
- Maturity level (draft, validated, production)
- API dependencies
- Anonymization readiness
- Client view enablement
- Industry benchmark eligibility
