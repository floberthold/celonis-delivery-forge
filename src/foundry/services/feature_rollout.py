"""Compatibility shim for rollout profile helpers.

Prefer importing from foundry.services.platform.feature_rollout.
"""

from __future__ import annotations

from foundry.services.platform.feature_rollout import (  # noqa: F401
    DEFAULT_PROFILE,
    enabled_domains_for_org,
    resolve_rollout_profile,
)
