from __future__ import annotations

import json
import os

import pytest

from tests.e2e.helpers import append_bug, prepare_run, write_metadata


pytestmark = pytest.mark.e2e


def _is_enabled() -> bool:
    return os.getenv("RUN_PLAYWRIGHT_E2E") == "1"


def _adapter_base_url() -> str:
    return os.getenv("LOCAL_WIKI_QUERY_BASE_URL", "http://127.0.0.1:8008").rstrip("/")


def test_playwright_local_wiki_query_chat_completion_is_grounded() -> None:
    if not _is_enabled():
        pytest.skip("Set RUN_PLAYWRIGHT_E2E=1 to execute browser E2E journeys.")

    playwright = pytest.importorskip("playwright.sync_api")
    base_url = _adapter_base_url()

    metadata, run_dir = prepare_run("local-wiki-query-adapter-grounded", browser="chromium")

    try:
        with playwright.sync_playwright() as p:
            request_context = p.request.new_context(base_url=base_url)

            health_response = request_context.get("/health", timeout=15_000)
            if not health_response.ok:
                pytest.skip("Local wiki query adapter health check failed.")

            models_response = request_context.get("/v1/models", timeout=20_000)
            assert models_response.ok
            model_id = models_response.json()["data"][0]["id"]
            assert model_id.startswith("local-wiki-query/")

            invalid_completion_response = request_context.post(
                "/v1/chat/completions",
                data=json.dumps(
                    {
                        "model": "smollm2:135m",
                        "messages": [
                            {
                                "role": "user",
                                "content": "What is Celonis in this repository context?",
                            }
                        ],
                        "stream": False,
                        "use_ollama": False,
                        "limit": 5,
                    }
                ),
                headers={"Content-Type": "application/json"},
                timeout=30_000,
            )
            assert invalid_completion_response.status == 400

            completion_response = request_context.post(
                "/v1/chat/completions",
                data=json.dumps(
                    {
                        "model": model_id,
                        "messages": [
                            {
                                "role": "user",
                                "content": "What is Celonis in this repository context? Answer only from retrieved wiki context and cite sources.",
                            }
                        ],
                        "stream": False,
                        "use_ollama": False,
                        "limit": 5,
                    }
                ),
                headers={"Content-Type": "application/json"},
                timeout=90_000,
            )
            assert completion_response.ok

            payload = completion_response.json()
            content = payload["choices"][0]["message"]["content"]

            has_sources = "### Sources" in content

            if not has_sources:
                append_bug(
                    run_dir,
                    severity="P1",
                    expected_behavior="Chat completion should be grounded and include citations for Celonis query.",
                    observed_behavior="Chat completion did not include expected grounded source markers.",
                    route="/v1/chat/completions",
                )
                metadata.status = "failed"
            else:
                metadata.status = "passed"

            write_metadata(run_dir, metadata)

            assert has_sources
    except Exception:
        metadata.status = "failed"
        write_metadata(run_dir, metadata)
        raise
