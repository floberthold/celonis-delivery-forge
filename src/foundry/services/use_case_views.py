"""Compatibility shim for use-case view adapters.

Prefer importing from foundry.services.knowledge.use_case_views.
"""

from __future__ import annotations

from foundry.services.knowledge.use_case_views import (  # noqa: F401
    to_industry_benchmark_summary,
    to_view_payload,
)
