# ⚡ Quick Start

## 1-Minute Startup

```powershell
.\START.ps1
```

That's it. The script will:
1. Install dependencies (if needed)
2. Start the API server
3. Open the dashboard in your browser

**Server:** http://127.0.0.1:8000

Press `Ctrl+C` to stop.

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

### Use a Different Port
Edit `START.ps1` or run manually:
```powershell
uvicorn foundry.api.main:app --reload --port 9000
```

### View Server Logs
Logs are saved to: `AppData\Local\CelonisDeliveryForge\desktop.log`

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
