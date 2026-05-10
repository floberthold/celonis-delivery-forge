from __future__ import annotations

import os

import httpx
import pytest


def _live_mode_enabled() -> bool:
    return os.getenv("RUN_LOCAL_WIKI_QUERY_LIVE") == "1"


def _base_url() -> str:
    return os.getenv("LOCAL_WIKI_QUERY_BASE_URL", "http://127.0.0.1:8008").rstrip("/")


def _require_live_service() -> str:
    if not _live_mode_enabled():
        pytest.skip("Set RUN_LOCAL_WIKI_QUERY_LIVE=1 to execute live local wiki query contract tests.")

    base_url = _base_url()
    try:
        response = httpx.get(f"{base_url}/health", timeout=10.0)
        response.raise_for_status()
    except httpx.HTTPError:
        pytest.skip("Local wiki query service is not reachable.")

    return base_url


def test_local_wiki_query_health_contract_live() -> None:
    base_url = _require_live_service()

    response = httpx.get(f"{base_url}/health", timeout=10.0)
    response.raise_for_status()
    payload = response.json()

    assert payload["status"] == "ok"
    assert isinstance(payload.get("document_count"), int)
    assert payload["document_count"] > 0


def test_local_wiki_query_search_returns_celonis_hits_live() -> None:
    base_url = _require_live_service()

    response = httpx.post(
        f"{base_url}/search",
        json={"query": "celonis", "limit": 5},
        timeout=30.0,
    )
    response.raise_for_status()
    payload = response.json()

    hits = payload.get("hits", [])
    assert hits
    assert any("celonis" in (hit.get("title", "") + hit.get("path", "")).lower() for hit in hits)


def test_local_wiki_query_openai_chat_completions_includes_sources_live() -> None:
    base_url = _require_live_service()

    models_response = httpx.get(f"{base_url}/v1/models", timeout=20.0)
    models_response.raise_for_status()
    models_payload = models_response.json()
    model_id = models_payload["data"][0]["id"]
    assert model_id.startswith("local-wiki-query/")

    response = httpx.post(
        f"{base_url}/v1/chat/completions",
        json={
            "model": model_id,
            "messages": [
                {
                    "role": "user",
                    "content": "What is Celonis in this repository context? Answer only from retrieved wiki context and cite sources.",
                }
            ],
            "stream": False,
            "limit": 5,
            "use_ollama": False,
        },
        timeout=60.0,
    )
    response.raise_for_status()
    payload = response.json()

    assert payload["object"] == "chat.completion"
    content = payload["choices"][0]["message"]["content"]
    assert "### Sources" in content
    assert "Celonis" in content or "celonis" in content


def test_local_wiki_query_rejects_non_namespaced_model_id_live() -> None:
    base_url = _require_live_service()

    response = httpx.post(
        f"{base_url}/v1/chat/completions",
        json={
            "model": "smollm2:135m",
            "messages": [
                {
                    "role": "user",
                    "content": "What is Celonis in this repository context?",
                }
            ],
            "stream": False,
            "limit": 5,
            "use_ollama": False,
        },
        timeout=60.0,
    )

    assert response.status_code == 400
    payload = response.json()
    assert "Unsupported model id" in payload["detail"]
