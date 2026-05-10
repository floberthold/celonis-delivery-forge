from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path


DEFAULT_PROFILE = "full"


def _default_rollout_config() -> dict:
    return {
        "default_profile": DEFAULT_PROFILE,
        "profiles": {
            "full": {
                "enabled_domains": [
                    "*",
                ]
            },
            "pilot-core": {
                "enabled_domains": [
                    "core-platform",
                ]
            },
            "pilot-core-plus-knowledge": {
                "enabled_domains": [
                    "core-platform",
                    "knowledge-hub",
                ]
            },
            "integration-celonis": {
                "enabled_domains": [
                    "core-platform",
                    "celonis-agent",
                ]
            },
        },
        "org_profile_overrides": {},
    }


@lru_cache(maxsize=1)
def _load_rollout_file(config_path: str) -> dict:
    fallback = _default_rollout_config()
    path = Path(config_path)
    if not path.exists():
        return fallback

    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return fallback

    if not isinstance(raw, dict):
        return fallback

    profiles = raw.get("profiles")
    if not isinstance(profiles, dict) or not profiles:
        return fallback

    return {
        "default_profile": str(raw.get("default_profile") or fallback["default_profile"]),
        "profiles": profiles,
        "org_profile_overrides": raw.get("org_profile_overrides") or {},
    }


def resolve_rollout_profile(config_path: str, org_slug: str | None) -> str:
    config = _load_rollout_file(config_path)
    overrides = config.get("org_profile_overrides", {})
    if org_slug and isinstance(overrides, dict):
        override_profile = overrides.get(org_slug)
        if isinstance(override_profile, str) and override_profile in config["profiles"]:
            return override_profile

    default_profile = config.get("default_profile", DEFAULT_PROFILE)
    if isinstance(default_profile, str) and default_profile in config["profiles"]:
        return default_profile
    return DEFAULT_PROFILE


def enabled_domains_for_org(config_path: str, org_slug: str | None) -> list[str]:
    config = _load_rollout_file(config_path)
    profile = resolve_rollout_profile(config_path, org_slug)
    profile_data = config.get("profiles", {}).get(profile, {})

    enabled_domains = profile_data.get("enabled_domains", ["*"])
    if not isinstance(enabled_domains, list) or not enabled_domains:
        return ["*"]

    result: list[str] = []
    for domain in enabled_domains:
        if isinstance(domain, str):
            result.append(domain)

    return result or ["*"]
