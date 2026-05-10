# Startup Guide

## Files in This Project

- **`START.ps1`** - PowerShell startup script (Recommended for Windows)
- **`START.bat`** - Batch file startup script (Alternative for Windows)
- **`QUICKSTART.md`** - 1-minute quick reference
- **`README.md`** - Full documentation and configuration

## How to Start

### 🟢 Recommended (Tool Hub, One-Click)

Run this once:

```powershell
.\START.ps1
```

Default mode starts the centralized Tool Hub:
1. Loads central registry from `agentic/tool-hub/tool_hub_registry.json`
2. Starts all enabled tools across main repo/submodules
3. Writes runtime state and logs under `.orchestration/tool-hub/`
4. Keeps Foundry API available at `http://127.0.0.1:8000`

Implementation paths:
- `agentic/tool-hub/start_tool_hub.ps1`
- `agentic/tool-hub/tool_hub_registry.json`

Compatibility wrapper:
- `scripts/start_tool_hub.ps1` forwards to the new location.

Useful commands:

```powershell
# dry run (discovery + validation, no process start)
.\START.ps1 -Mode dry-run

# include auto-discovered START scripts/manifests from submodules
.\START.ps1 -Mode dry-run -IncludeAutoDiscovered

# show current process status
.\START.ps1 -Mode status

# stop all tool-hub started processes
.\START.ps1 -Mode stop
```

Legacy behavior is still available:

```powershell
.\START.ps1 -Mode api-only
```

### 🔵 Alternative (Manual API Startup)

If you prefer to run each step manually:

```powershell
# Step 1: Install dependencies (one time only)
python -m pip install --upgrade pip
python -m pip install -e .

# Step 2: Start the server
uvicorn foundry.api.main:app --reload

# Step 3: Open browser
# Go to: http://127.0.0.1:8000
```

---

## After Startup

### 🎯 What You Can Access

| URL | What It Is |
|-----|-----------|
| `http://127.0.0.1:8000/` | **Main Dashboard** (Start here!) |
| `http://127.0.0.1:8000/celonis-tool-hub-ui` | Celonis Tool Hub UI |
| `http://127.0.0.1:8000/docs` | API Documentation (Swagger) |
| `http://127.0.0.1:8000/health` | Health Status Check |

### 📖 Documentation

Inside the running app:
- User Guide: `http://127.0.0.1:8000/docs-site/user/`
- Developer Guide: `http://127.0.0.1:8000/docs-site/developer/`

---

## Common Issues

### "Python not found"
Make sure Python 3.11+ is installed and in your PATH.
```powershell
python --version
```

### "Module not found" errors
Dependencies might not have installed. Run:
```powershell
python -m pip install -e .
```

### "Port 8000 already in use"
Another app is using port 8000. Either:
- Stop the other app, or
- Use a different port: `uvicorn foundry.api.main:app --reload --port 9000`

### Server starts but dashboard won't load
Give it a moment (15-30 seconds) on first startup. The API needs to initialize the database.

### Changes to code aren't showing up
The server has auto-reload enabled. Just save the file and it will restart automatically. Wait for the "Application startup complete" message.

---

## Configuration (Optional)

For most users, nothing is needed. But if you want to customize:

### SMTP (for email features)
```powershell
$env:FORGE_SMTP_HOST="smtp.office365.com"
$env:FORGE_SMTP_PORT="587"
$env:FORGE_SMTP_USERNAME="your-email@company.com"
$env:FORGE_SMTP_PASSWORD="your-password"
$env:FORGE_SMTP_FROM_EMAIL="noreply@company.com"
```

### Celonis Integration
```powershell
$env:FORGE_CELONIS_API_TOKEN="your-celonis-token"
```

### Use External Database (PostgreSQL)
```powershell
$env:FORGE_DATABASE_URL="postgresql://user:password@localhost/forge_db"
```

For full config options, see `README.md`.

---

## Need Help?

1. Check the logs: `AppData\Local\CelonisDeliveryForge\desktop.log`
2. Try restarting: `Ctrl+C` then `.\START.ps1`
3. Read full docs in `README.md`
4. Check `src/` for source code
