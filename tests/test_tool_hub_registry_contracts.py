import json
from pathlib import Path


REGISTRY_PATH = Path("agentic/tool-hub/tool_hub_registry.json")
ALLOWED_HEALTH_PROBE_TYPES = {"http", "process"}


def _load_registry_tools() -> list[dict]:
    payload = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    tools = payload.get("tools", [])
    return [tool for tool in tools if isinstance(tool, dict)]


def test_tool_hub_registry_tools_define_contract_fields() -> None:
    tools = _load_registry_tools()
    assert tools

    for tool in tools:
        assert isinstance(tool.get("id"), str) and tool["id"].strip()
        assert isinstance(tool.get("display_name"), str) and tool["display_name"].strip()
        assert isinstance(tool.get("domain"), str) and tool["domain"].strip()
        assert isinstance(tool.get("repo_path"), str) and tool["repo_path"].strip()
        assert isinstance(tool.get("shell"), str) and tool["shell"].strip()
        assert isinstance(tool.get("command"), str) and tool["command"].strip()
        assert isinstance(tool.get("enabled"), bool)


def test_tool_hub_registry_health_probe_contracts_are_valid() -> None:
    tools = _load_registry_tools()

    for tool in tools:
        probe = tool.get("health_probe")
        assert isinstance(probe, dict), f"health_probe missing or invalid for tool {tool.get('id')}"
        probe_type = probe.get("type")
        assert probe_type in ALLOWED_HEALTH_PROBE_TYPES, f"invalid health_probe.type for tool {tool.get('id')}"

        if probe_type == "http":
            assert isinstance(probe.get("url"), str) and probe["url"].strip(), (
                f"http health probe must define url for tool {tool.get('id')}"
            )


def test_tool_hub_registry_activation_phase_is_positive_integer_when_present() -> None:
    for tool in _load_registry_tools():
        if "activation_phase" not in tool:
            continue
        phase = int(tool["activation_phase"])
        assert phase >= 1, f"activation_phase must be >= 1 for tool {tool.get('id')}"
