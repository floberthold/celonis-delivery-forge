# Quick Wiki Update

Use this when you just want to refresh the wiki from current raw notes.

Default behavior: every run now updates the wiki and regenerates strict bundle notes under `wiki/projects/`.

## 1. Start Ollama

Make sure Ollama is running before updating.

## 2. Run the updater

From this folder (`external resources/local-knowledge-model`):

```powershell
.\update-wiki.ps1
```

That updates the default vault:

- `my-obsidian-wiki`

You will see live step output:

- `Ingest`
- `Compile`
- `Lint`
- `All Bundles (clients/apps/ideas)`

Important:

- Standard runs now also regenerate project/client/app/idea/people bundles.

## 3. Optional: use a different vault path

```powershell
.\update-wiki.ps1 -VaultPath "C:\path\to\your\vault"
```

## 4. Force project bundle creation in the same run

Use this to update the wiki and then create/update the Fuchs project bundle immediately:

```powershell
.\update-wiki.ps1 -BuildProjectBundle
```

Custom project question:

```powershell
.\update-wiki.ps1 -BuildProjectBundle -ProjectQuestion "what celonis projects do we have running at fuchs?"
```

## 5. Build bundles for all discoverable clients, apps, and ideas

This now runs automatically in standard updates.

You can still force only the bundle step explicitly if needed:

```powershell
.\update-wiki.ps1 -BuildAllBundles
```

This creates or updates:

- `wiki/projects/<client>-projects.md` (for discoverable clients)
- `wiki/projects/all-projects.md`
- `wiki/projects/all-apps.md`
- `wiki/projects/all-ideas.md`
- `wiki/projects/all-people.md`

## 6. Optional: skip bundle generation

If you only want ingest/compile/lint for a quick run:

```powershell
.\update-wiki.ps1 -SkipBundleGeneration
```

## Notes

- The script first tries `obsidian-llm-wiki-local/.venv/Scripts/python.exe`.
- If that does not exist, it uses `local-llm-wiki-query/.venv/Scripts/python.exe`.
- Otherwise it falls back to `python` from PATH.
- If PowerShell blocks script execution, run:

```powershell
powershell -ExecutionPolicy Bypass -File .\update-wiki.ps1
```
