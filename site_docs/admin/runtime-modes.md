# Runtime Modes

Choose runtime mode based on team size, persistence requirements, and deployment target.

## Local Python Mode

Use for day-to-day development and quick functional checks.

Start command:

```powershell
uvicorn foundry.api.main:app --reload
```

Characteristics:

- Fast iteration with reload.
- Uses configured DB, may fallback to local sqlite in dev/local.
- Best mode for debugging routes and templates.

## Desktop Mode

Use for local app-style startup.

Start command:

```powershell
python -m foundry.desktop.app
```

Characteristics:

- Starts local API process.
- Opens browser automatically.
- Writes logs to `%LOCALAPPDATA%/CelonisDeliveryForge/desktop.log`.

## Standalone EXE Mode

Use for distribution on Windows without manual Python startup.

Build command:

```powershell
.\scripts\build_standalone.ps1
```

Run options:

- `scripts/run_standalone.vbs` (hidden)
- `scripts/run_standalone.bat`
- `scripts/run_standalone_debug.bat`

## Docker Compose Mode

Use for integration testing with bundled Postgres service.

Start command:

```powershell
docker compose up --build
```

Characteristics:

- Deterministic service composition.
- Postgres is provisioned as a container.
- Good for validating non-sqlite behavior.

## Runtime Verification

For any mode, verify:

1. `/health` returns `status: ok`.
2. `/docs-site/` is served.
3. `/login` and `/dashboard` are reachable.
4. DB backend/mode in `/health` matches your expectation.
