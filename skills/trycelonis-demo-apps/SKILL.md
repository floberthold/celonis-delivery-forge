---
name: trycelonis-demo-apps
description: Discover TryCelonis demo applications, scaffold demo rebuild repositories, and manage demo asset versioning.
---

# TryCelonis Demo Apps Skill

Use this skill when an agent needs to:

- Discover available demos from TryCelonis catalog.
- Bootstrap demo rebuild repositories locally.
- Create variant branches for demos (v2, v3, etc.).
- Export and analyze demo inventory and asset breakdown.
- Track demo maturity and complexity levels.

## Tool usage order

1. Discover demos from catalog:
   - `python scripts/trycelonis_demo_apps.py discover <catalog-url>`
2. Bootstrap locally:
   - `python scripts/trycelonis_demo_apps.py bootstrap --output <dir>`
3. Create variant:
   - `python scripts/trycelonis_demo_apps.py variant --demo-id <id> --variant-name <name>`
4. Export inventory:
   - `python scripts/trycelonis_demo_apps.py inventory --format json`

## Expected outputs

- Demo catalog (`.orchestration/demos/catalog.json`).
- Space inventory snapshot (`.orchestration/demos/inventory.json`).
- Bootstrap directories with demo configurations.
- Variant branch manifests.

## Safety rules

- Preserve demo asset versions and provenance.
- Include industry and complexity metadata in inventory.
- Document demo dependencies and prerequisites.
- Maintain asset attribution and licensing information.
- Track demo rebuild history for reproducibility.
