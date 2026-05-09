# Celonis Delivery Forge - Startup Checklist

Use this as a visual guide for what to expect during startup.

## Step-by-Step Startup

### 1️⃣ Run the Startup Script

**PowerShell:**
```powershell
.\START.ps1
```

**Command Prompt:**
```cmd
START.bat
```

You'll see something like:
```
================================
Celonis Delivery Forge - Startup
================================

Step 1: Checking dependencies...
  ✓ Dependencies already installed

Step 2: Starting API server...
  Server starting on http://127.0.0.1:8000
  Press Ctrl+C to stop the server

INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [12345]
INFO:     Started server process [67890]
INFO:     Waiting for application startup.
Configured database is unavailable during startup; falling back to local database
INFO:     Application startup complete.
```

✅ **All good!** The server is running.

### 2️⃣ Open Your Browser

Automatically opens to: `http://127.0.0.1:8000/`

You should see the **Celonis Delivery Forge Dashboard**

### 3️⃣ You're Done! 🎉

Work with the app. The server will:
- 🔄 Auto-reload when you change code
- 📝 Log activities to the console
- 💾 Store data in local SQLite database

### 4️⃣ To Stop

Press `Ctrl+C` in the terminal

```
^C
INFO:     Shutting down
INFO:     Shutdown complete
PS C:\path\to\celonis-delivery-forge>
```

---

## What's Running?

### On Startup
- ✅ FastAPI Server (Python web framework)
- ✅ Uvicorn (ASGI server)
- ✅ SQLite Database (local file)
- ✅ Jinja2 Templates (HTML rendering)

### Available URLs
| URL | Opens |
|-----|-------|
| `http://127.0.0.1:8000/` | Dashboard (main UI) |
| `http://127.0.0.1:8000/docs` | API Docs (Swagger) |
| `http://127.0.0.1:8000/health` | Server Health Status |
| `http://127.0.0.1:8000/docs-site/` | Full Documentation |

### Database Location
```
C:\Users\[YourUsername]\AppData\Local\CelonisDeliveryForge\
  ├── foundry.db          (SQLite database)
  └── desktop.log         (Server logs)
```

---

## Expected Console Output

### Normal Startup (Everything OK)
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete.
```

### If You See This...
```
Configured database is unavailable during startup; falling back to local database
```
→ This is **normal** and **OK**. The app uses a local SQLite database.

### After You Make Code Changes
```
INFO:     Detected file change in 'src/foundry/api/main.py'. Reloading...
INFO:     Shutting down
INFO:     Shutdown complete
INFO:     Uvicorn reloading in workspace mode
INFO:     Application startup complete.
```
→ The server **reloads automatically**. No action needed.

---

## Troubleshooting

### Issue: "Python not found"
```
'python' is not recognized as an internal or external command
```
**Fix:** Install Python 3.11+ from [python.org](https://python.org) or add it to PATH.

### Issue: "Port 8000 already in use"
```
[Errno 10048] Only one usage of each socket address
```
**Fix:** 
- Another server is running on port 8000
- Either stop it, or use a different port: `--port 9000`

### Issue: "ModuleNotFoundError: No module named 'foundry'"
**Fix:** Dependencies didn't install. Run:
```powershell
python -m pip install -e .
```

### Issue: Dashboard loads but says "Waiting..."
**Fix:** 
- Give it 10-30 seconds on first startup
- Check the console for errors
- Try `Ctrl+C` and restart

### Issue: Code changes aren't showing up
**Fix:**
- Wait for "Application startup complete" message in console
- Reload browser (F5)
- If still not working, stop (`Ctrl+C`) and restart

---

## Tips & Tricks

### 🚀 Fast Restart
```powershell
Ctrl+C  # Stop server
.\START.ps1  # Restart
```

### 📝 View Real-Time Logs
Logs appear in the terminal as they happen. For saved logs:
```powershell
cat $env:LOCALAPPDATA\CelonisDeliveryForge\desktop.log
```

### 🧪 Test the API
```powershell
# In a new terminal:
curl http://127.0.0.1:8000/health
```

### 🔌 Use Different Port
```powershell
uvicorn foundry.api.main:app --reload --port 9000
```

### 💾 Use External Database
```powershell
$env:FORGE_DATABASE_URL="postgresql://user:pass@localhost/forge"
uvicorn foundry.api.main:app --reload
```

---

## Success! 🎉

Your development environment is ready. Happy coding!
