# Action Flow Template Library

This library stores Make-inspired reusable action-flow assets for Delivery Forge.

## Structure

- `schema/` contains versioned structured schema contracts.
- `catalog/` contains machine-readable index files.
- `specs/` contains template implementation specs.
- `playbooks/` contains consultant-friendly setup and rollout guidance.

## Design principles

- Keep every template deterministic where possible.
- Make retries and dead-letter behavior explicit.
- Require ownership and review cadence metadata.
- Preserve audit evidence for every rollout.

## Current release

- Schema version: `1.0.0`
- Template packs: 12 starter templates
- Families: alerts/escalation, sync/propagation, recommendation/human-loop, AI-assisted triage
