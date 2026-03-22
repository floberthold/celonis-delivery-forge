# Open-Source Upstream Workflow (Submodule + Forge Layer)

This project can vendor open-source code as a git submodule and keep Delivery Forge customizations as a separate layer on top.

## Why this pattern

- Keeps third-party code history and licensing boundaries clear
- Makes upstream updates deterministic
- Avoids mixing local product logic with vendored source

## Add a new upstream

Run from repo root:

```powershell
.\scripts\add_upstream_submodule.ps1 -UpstreamUrl "https://github.com/<owner>/<repo>.git" -Name "<alias>" -Branch "main"
```

What this does:

- Adds a submodule under `vendor/<alias>`
- Initializes and pins the exact baseline commit
- Creates metadata in `.upstreams/<alias>.json`
- Creates a patch queue folder in `patches/<alias>/`

## Where custom code should live

Keep custom logic in first-party paths such as:

- `src/foundry/integrations/`
- `src/foundry/services/`
- `src/foundry/ui/`

Avoid editing the submodule directly unless absolutely necessary.

## If upstream patching is unavoidable

- Create patch files from a fork or from a temporary branch in the submodule
- Store patch artifacts in `patches/<alias>/`
- Document why the patch exists and when it should be dropped

## Upgrade flow

1. Update submodule to a new upstream commit/branch.
2. Re-run tests against Forge adapters.
3. Re-apply and prune patch queue if needed.
4. Commit gitlink + metadata changes together.

## Suggested commit structure

- Commit 1: `chore(upstream): add <alias> submodule at <commit>`
- Commit 2: `feat(integration): add Forge adapter for <alias>`
- Commit 3 (optional): `fix(upstream-patch): patch <alias> for <reason>`
