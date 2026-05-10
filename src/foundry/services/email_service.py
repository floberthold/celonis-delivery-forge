"""Compatibility shim for email delivery service.

Prefer importing from foundry.services.integrations.email_service.
"""

from __future__ import annotations

from foundry.services.integrations.email_service import send_email  # noqa: F401
