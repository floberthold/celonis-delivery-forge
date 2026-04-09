# Sales

The Sales workspace gives delivery and sales teams one governed overview of TryCelonis partner demos.

## Purpose

Use `/sales-ui` to:

- sync the current TryCelonis demo catalog into the Forge database
- review the demos that are available for rebuild
- open the original external source for each demo
- decide which demo should get its own repository and customer-specific branch

## What Is Stored

Forge stores overview data only:

- title
- slug
- summary
- industries
- tags
- confidence score
- original source URL
- last synced timestamp

## Why This Matters

The TryCelonis partner portal is valuable for demo discovery, but those demos are not available as ready-made Marketplace assets. Forge uses the catalog as input for a managed rebuild workflow:

1. identify the demo
2. save the overview and source link
3. rebuild the demo in a managed repository
4. create a customer-specific branch
5. deploy it into the shared sandbox space only when needed

## Source Modes

- Live catalog crawl: use when the portal exposes readable demo records directly.
- Manifest import: use when the portal is gated and you need to import a curated manifest exported from an authenticated session.

## Related Setup

Admin connection details are documented in [Admin Full Setup](../admin/full-setup.md) and [Configuration Reference](../getting-started/configuration-reference.md).