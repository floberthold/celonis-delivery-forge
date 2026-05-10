import json
from pathlib import Path


def test_tool_hub_registry_includes_local_knowledge_tools() -> None:
    registry_path = Path("agentic/tool-hub/tool_hub_registry.json")
    payload = json.loads(registry_path.read_text(encoding="utf-8"))

    tools = payload.get("tools", [])
    by_id = {tool.get("id"): tool for tool in tools if isinstance(tool, dict)}

    local_query = by_id.get("local-wiki-query-api")
    assert local_query is not None
    assert local_query.get("enabled") is True
    assert local_query.get("repo_path") == "."
    local_query_command = str(local_query.get("command", ""))
    assert "local-llm-wiki-query" in local_query_command
    assert "uvicorn" in local_query_command

    open_webui = by_id.get("local-wiki-open-webui")
    assert open_webui is not None
    assert open_webui.get("enabled") is True
    assert open_webui.get("repo_path") == "."
    assert "start_open_webui_local_knowledge.ps1" in str(open_webui.get("command", ""))
