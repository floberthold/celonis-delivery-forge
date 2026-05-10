import httpx
import pytest

from foundry.services.local_knowledge_gateway import (
    LocalKnowledgeGateway,
    LocalKnowledgeGatewayError,
    LocalKnowledgeGatewayUnavailable,
)
from foundry.settings import Settings


def _settings(**overrides) -> Settings:
    base = {
        "local_knowledge_enabled": True,
        "local_knowledge_query_base_url": "http://127.0.0.1:8008",
        "local_knowledge_timeout_seconds": 10,
    }
    base.update(overrides)
    return Settings(**base)


def test_gateway_health_success() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert request.url.path == "/health"
        return httpx.Response(
            status_code=200,
            json={"status": "ok", "document_count": 10, "ollama_available": True},
        )

    transport = httpx.MockTransport(handler)
    gateway = LocalKnowledgeGateway(_settings(), transport=transport)

    payload = gateway.health()

    assert payload["status"] == "ok"
    assert payload["document_count"] == 10


def test_gateway_search_passes_payload() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url.path == "/search"
        assert request.read() == b'{"query":"celonis","limit":3}'
        return httpx.Response(status_code=200, json={"query": "celonis", "hits": []})

    transport = httpx.MockTransport(handler)
    gateway = LocalKnowledgeGateway(_settings(), transport=transport)

    payload = gateway.search(query="celonis", limit=3)

    assert payload["query"] == "celonis"
    assert payload["hits"] == []


def test_gateway_unavailable_when_disabled() -> None:
    gateway = LocalKnowledgeGateway(_settings(local_knowledge_enabled=False))

    with pytest.raises(LocalKnowledgeGatewayUnavailable):
        gateway.health()


def test_gateway_maps_404_to_file_not_found() -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(status_code=404, json={"detail": "Document not found"})

    transport = httpx.MockTransport(handler)
    gateway = LocalKnowledgeGateway(_settings(), transport=transport)

    with pytest.raises(FileNotFoundError):
        gateway.document("wiki/missing.md")


def test_gateway_maps_non_404_to_gateway_error() -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(status_code=500, json={"detail": "boom"})

    transport = httpx.MockTransport(handler)
    gateway = LocalKnowledgeGateway(_settings(), transport=transport)

    with pytest.raises(LocalKnowledgeGatewayError):
        gateway.corpus()
