import json
from pathlib import Path


REGISTRY_PATH = Path("agentic/tool-hub/tool_hub_registry.json")
PROFILES_PATH = Path("agentic/tool-hub/tool_hub_profiles.json")


def _load_registry_tools() -> list[dict]:
    payload = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    return list(payload.get("tools", []))


def _load_profile(profile_id: str) -> dict:
    payload = json.loads(PROFILES_PATH.read_text(encoding="utf-8"))
    profiles = payload.get("profiles", [])
    for profile in profiles:
        if profile.get("id") == profile_id:
            return profile
    raise AssertionError(f"Profile not found: {profile_id}")


def _effective_enabled_tools(profile_id: str) -> list[dict]:
    profile = _load_profile(profile_id)
    include_domains = profile.get("include_domains", [])
    include_tool_ids = profile.get("include_tool_ids", [])
    exclude_tool_ids = profile.get("exclude_tool_ids", [])
    max_activation_phase = int(profile.get("max_activation_phase", 99))
    allows_all_domains = "*" in include_domains

    enabled_tools: list[dict] = []
    for tool in _load_registry_tools():
        if not bool(tool.get("enabled", False)):
            continue

        tool_id = str(tool.get("id", ""))
        tool_domain = str(tool.get("domain", "unassigned"))
        tool_activation_phase = int(tool.get("activation_phase", 1) or 1)
        domain_allowed = allows_all_domains or not include_domains or tool_domain in include_domains
        explicit_tool_included = tool_id in include_tool_ids
        tool_excluded = tool_id in exclude_tool_ids
        phase_allowed = tool_activation_phase <= max_activation_phase

        profile_allows_tool = (domain_allowed or explicit_tool_included) and not tool_excluded and phase_allowed
        if profile_allows_tool:
            enabled_tools.append(tool)

    return enabled_tools


def test_pilot_core_profile_enables_only_core_platform_tools() -> None:
    enabled_tools = _effective_enabled_tools("pilot-core")
    assert enabled_tools, "pilot-core should enable at least one core tool"
    assert all(tool.get("domain") == "core-platform" for tool in enabled_tools)


def test_pilot_core_plus_knowledge_enables_core_and_knowledge_tools() -> None:
    enabled_tools = _effective_enabled_tools("pilot-core-plus-knowledge")
    enabled_domains = {str(tool.get("domain")) for tool in enabled_tools}
    assert "core-platform" in enabled_domains
    assert "knowledge-hub" in enabled_domains
    assert enabled_domains.issubset({"core-platform", "knowledge-hub"})


def test_integration_celonis_profile_enables_core_and_celonis_tools() -> None:
    enabled_tools = _effective_enabled_tools("integration-celonis")
    enabled_domains = {str(tool.get("domain")) for tool in enabled_tools}
    assert "core-platform" in enabled_domains
    assert "celonis-agent" in enabled_domains
    assert enabled_domains.issubset({"core-platform", "celonis-agent"})


def test_full_profile_enables_all_registry_enabled_tools() -> None:
    enabled_tools = _effective_enabled_tools("full")
    registry_enabled = [tool for tool in _load_registry_tools() if bool(tool.get("enabled", False))]

    assert {tool["id"] for tool in enabled_tools} == {tool["id"] for tool in registry_enabled}
