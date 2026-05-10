from __future__ import annotations

import os

import httpx
import pytest

from tests.e2e.helpers import append_bug, prepare_run, write_metadata


pytestmark = pytest.mark.e2e


def test_playwright_scaffold_dashboard_login_journey() -> None:
    if os.getenv("RUN_PLAYWRIGHT_E2E") != "1":
        pytest.skip("Set RUN_PLAYWRIGHT_E2E=1 to execute browser E2E journeys.")

    base_url = os.getenv("FORGE_E2E_BASE_URL", "http://127.0.0.1:8000").rstrip("/")
    try:
        health = httpx.get(f"{base_url}/health", timeout=3.0)
        if health.status_code >= 500:
            pytest.skip("E2E base URL is not healthy.")
    except httpx.HTTPError:
        pytest.skip("E2E base URL is not reachable.")

    playwright = pytest.importorskip("playwright.sync_api")
    metadata, run_dir = prepare_run("dashboard-login-smoke", browser="chromium")

    screenshot_path = run_dir / "dashboard-login.png"
    trace_path = run_dir / "dashboard-login-trace.zip"

    with playwright.sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(base_url=base_url)
        context.tracing.start(screenshots=True, snapshots=True, sources=False)
        page = context.new_page()
        page.goto("/login")

        h2 = page.locator("h2")
        has_login_heading = h2.count() > 0 and h2.first.inner_text().strip().lower() == "login"
        page.screenshot(path=str(screenshot_path), full_page=True)
        context.tracing.stop(path=str(trace_path))
        browser.close()

    if not has_login_heading:
        append_bug(
            run_dir,
            severity="P1",
            expected_behavior="Login heading should be visible on /login",
            observed_behavior="Could not validate expected login heading content",
            route="/login",
            evidence=[str(screenshot_path), str(trace_path)],
        )
        metadata.status = "failed"
    else:
        metadata.status = "passed"

    write_metadata(run_dir, metadata)
    assert has_login_heading
