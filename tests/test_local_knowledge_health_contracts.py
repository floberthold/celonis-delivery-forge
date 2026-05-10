from __future__ import annotations

from foundry.api.routes.local_knowledge import _normalize_health_status, _to_health_response


def test_normalize_health_status_maps_ok_to_healthy() -> None:
    assert _normalize_health_status("ok") == "healthy"
    assert _normalize_health_status("healthy") == "healthy"


def test_normalize_health_status_maps_unknown_to_unhealthy() -> None:
    assert _normalize_health_status("something-else") == "unhealthy"


def test_to_health_response_maps_gateway_payload() -> None:
    payload = _to_health_response(
        {
            "status": "ok",
            "version": "v2",
            "document_count": 42,
            "ollama_available": True,
        }
    )

    assert payload.status == "healthy"
    assert payload.version == "v2"
    assert payload.components["document_count"] == "42"
    assert payload.components["ollama_available"] == "True"
