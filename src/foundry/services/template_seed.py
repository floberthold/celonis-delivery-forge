"""Compatibility shim for template seed helpers.

Prefer importing from foundry.services.delivery.template_seed.
"""

from __future__ import annotations

from foundry.services.delivery.template_seed import (  # noqa: F401
    DEFAULT_LIBRARY_NAME,
    DEFAULT_TEMPLATES,
    seed_default_templates,
)
