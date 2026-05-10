# ⚡ Quick Start

## 1-Minute Startup

```powershell
.\START.ps1
```

That's it. The script will:
1. Load the central tool registry
2. Start all enabled tools in the Tool Hub
3. Write runtime state/logs to `.orchestration/tool-hub/`

**Server:** http://127.0.0.1:8000

Stop all started tool processes:

```powershell
.\START.ps1 -Mode stop
```

Discovery without starting processes:

```powershell
.\START.ps1 -Mode dry-run
```

Discovery with auto-discovered submodule startup entries:

```powershell
.\START.ps1 -Mode dry-run -IncludeAutoDiscovered
```

Legacy API-only mode:

```powershell
.\START.ps1 -Mode api-only
```

---

## What's Running?

| URL | Purpose |
|-----|---------|
| `http://127.0.0.1:8000` | **UI Dashboard** (main app) |
| `http://127.0.0.1:8000/docs` | API Documentation (Swagger) |
| `http://127.0.0.1:8000/health` | Health Check |
| `http://127.0.0.1:8000/docs-site/` | Full Documentation |

---

## Common Tasks

### Restart the Server
Just press `Ctrl+C` and run `.\START.ps1` again.

### Fast Developer Commands

Use the unified dev helper for fast loops:

```powershell
.\scripts\dev.ps1 -Action start-fast    # API fast start (no reload watcher)
.\scripts\dev.ps1 -Action test-smoke    # quick smoke tests
.\scripts\dev.ps1 -Action test-celonis  # Celonis focused tests
.\scripts\dev.ps1 -Action stop-all      # stop tool hub + related forge processes
.\scripts\dev.ps1 -Action reset         # stop + cleanup scan
.\scripts\dev.ps1 -Action repo-cleanup-scan
.\scripts\dev.ps1 -Action repo-cleanup-clean
```

Command Prompt wrapper:

```cmd
scripts\dev.bat start-fast
scripts\dev.bat test-smoke
scripts\dev.bat stop-all
```

### Use a Different Port
Edit `START.ps1` or run manually:
```powershell
uvicorn foundry.api.main:app --reload --port 9000
```

### View Server Logs
Logs are saved to: `AppData\Local\CelonisDeliveryForge\desktop.log`

### Repo Cleanup (Scan First)

```powershell
.\scripts\repo_cleanup.ps1 -Mode scan
```

Apply cleanup only when you are ready:

```powershell
.\scripts\repo_cleanup.ps1 -Mode clean
```

### Install New Dependencies
```powershell
python -m pip install -e .
```

---

## Manual Startup (if preferred)

```powershell
python -m pip install --upgrade pip
python -m pip install -e .
uvicorn foundry.api.main:app --reload
```

---

## Need Help?

- Check `README.md` for full documentation
- See `src/` for source code
- View logs at `AppData\Local\CelonisDeliveryForge\desktop.log`
