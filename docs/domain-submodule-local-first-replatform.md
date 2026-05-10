# Domain-Submodule Replatform (Local-First)

## Goal

Reduce runtime complexity without losing capabilities by running Delivery Forge as domain slices.

## Principles

- Local-first: all slices can run on a developer machine.
- Feature-complete by default: `full` profile keeps current behavior.
- Progressive rollout: pilot users start with a small slice and receive additional domains gradually.
- Stable contracts: each domain exposes explicit API/UI boundaries.

## Runtime Slices (Current)

- `core-platform`
  - Foundry API and core UI.
- `knowledge-hub`
  - Local wiki query API and Open WebUI adapter.
- `celonis-agent`
  - Celonis MCP and agent tooling.
- `data-utils`
  - Utility processes for data generation.
- `external-experiments`
  - Optional, non-core integrations and research utilities.

Domain mapping is maintained in `agentic/tool-hub/tool_hub_registry.json`.

## Activation Profiles

Profiles are maintained in `agentic/tool-hub/tool_hub_profiles.json`.

- `full`: all enabled tools.
- `pilot-core`: only `core-platform`.
- `pilot-core-plus-knowledge`: `core-platform` + `knowledge-hub`.
- `integration-celonis`: `core-platform` + `celonis-agent`.

## Rollout Model

1. Pilot A
- Profile: `pilot-core`
- Goal: validate baseline UX and workflows with lowest operational load.

2. Pilot B
- Profile: `pilot-core-plus-knowledge`
- Goal: add local knowledge workflows while keeping blast radius controlled.

3. Pilot C
- Profile: `integration-celonis`
- Goal: validate Celonis agent operations with selected users.

4. General Availability
- Profile: `full`
- Goal: all validated domains enabled.

## Operational Commands

```powershell
# validate active slice without starting processes
.\START.ps1 -Mode dry-run -Profile pilot-core

# start selected slice
.\START.ps1 -Profile pilot-core-plus-knowledge

# inspect running processes
.\START.ps1 -Mode status

# stop all processes
.\START.ps1 -Mode stop
```

## Next Hardening Steps

- Add profile-aware health summary in Tool Hub status output.
- Add per-profile acceptance test packs.
- Introduce profile-specific seed data for user testing.
- Add in-app feature flags mirroring startup domains for finer UI gating.
