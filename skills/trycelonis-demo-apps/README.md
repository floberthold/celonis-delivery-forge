# trycelonis-demo-apps skill

This skill discovers and catalogs TryCelonis demo applications, scaffolds demo rebuild repositories, and manages demo asset versioning.

## Quick start

```powershell
# Discover demos from catalog
python scripts/trycelonis_demo_apps.py discover https://discover.celonis.cloud/catalog

# Bootstrap demo repos locally
python scripts/trycelonis_demo_apps.py bootstrap --output ./demo-repos

# Create variant branch for a demo
python scripts/trycelonis_demo_apps.py variant --demo-id "order-to-cash-demo" --variant-name "v3-enhanced"

# Export demo inventory
python scripts/trycelonis_demo_apps.py inventory --format json
```

## Artifacts

- `.orchestration/demos/` - Demo catalog and metadata
- `.orchestration/demos/catalog.json` - Full demo catalog
- `.orchestration/demos/inventory.json` - Space inventory snapshot

## Demo Taxonomy

- Industries: Manufacturing, Finance, Logistics, etc.
- Asset types: dashboards, action flows, execution apps, KPIs
- Maturity: proof-of-concept, validated, production
- Complexity: basic, intermediate, advanced
