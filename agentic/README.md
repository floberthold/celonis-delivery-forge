# Agentic Folder

This folder contains orchestration and runtime assets for agent-driven workflows.

## Tool Hub

- `tool-hub/start_tool_hub.ps1`: central process orchestrator (start, dry-run, status, stop)
- `tool-hub/tool_hub_registry.json`: central registry for tool startup definitions
- `tool-hub/tool_hub_profiles.json`: activation profiles for domain-based startup slices

## Notes

- Root startup (`START.ps1`) invokes the tool hub from this folder.
- `scripts/start_tool_hub.ps1` is a compatibility wrapper that forwards to this folder.
