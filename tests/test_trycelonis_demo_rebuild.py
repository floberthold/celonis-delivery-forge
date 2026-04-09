from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

from foundry.services.trycelonis_demo_rebuild import (
    DemoCard,
    DemoCatalog,
    bootstrap_demo_repos,
    create_variant_branch,
    crawl_demo_catalog,
)


def test_crawl_demo_catalog_discovers_demo_pages() -> None:
    html_by_url = {
        "https://trycelonis.example/partners": """
            <html>
              <body>
                <a href="/demos/order-accelerator">Order Accelerator</a>
                <a href="/demos/claims-recovery">Claims Recovery Cockpit</a>
              </body>
            </html>
        """,
        "https://trycelonis.example/demos/order-accelerator": """
            <html>
              <head><title>Order Accelerator | TryCelonis</title></head>
              <body>
                <h1>Order Accelerator</h1>
                <p>Healthcare teams use this execution app to track orders, throughput time, and KPI exceptions.</p>
                <img src="/images/order.png" />
              </body>
            </html>
        """,
        "https://trycelonis.example/demos/claims-recovery": """
            <html>
              <head><title>Claims Recovery Cockpit</title></head>
              <body>
                <h1>Claims Recovery Cockpit</h1>
                <p>Automotive claims managers use this dashboard and action flow to prioritize reimbursement opportunities.</p>
              </body>
            </html>
        """,
    }

    catalog = crawl_demo_catalog(
        "https://trycelonis.example/partners",
        fetch_html=lambda url: html_by_url[url],
    )

    assert len(catalog.demos) == 2
    by_slug = {row.slug: row for row in catalog.demos}
    assert "order-accelerator" in by_slug
    assert "claims-recovery-cockpit" in by_slug
    assert "healthcare" in by_slug["order-accelerator"].industries
    assert "dashboard" in by_slug["claims-recovery-cockpit"].tags


@pytest.mark.skipif(shutil.which("git") is None, reason="git is required")
def test_bootstrap_demo_repos_creates_git_repos(tmp_path: Path) -> None:
    catalog = DemoCatalog(
        catalog_url="https://trycelonis.example/partners",
        generated_at="2026-03-22T00:00:00+00:00",
        demos=(
            DemoCard(
                name="Order Accelerator",
                slug="order-accelerator",
                source_url="https://trycelonis.example/demos/order-accelerator",
                summary="A demo app for healthcare order recovery.",
                industries=("healthcare",),
                tags=("execution-app",),
                confidence=0.75,
            ),
        ),
    )

    repos_root = tmp_path / "demo-repos"
    results = bootstrap_demo_repos(
        catalog,
        repos_root=repos_root,
        sandbox_space_name="TryCelonis Demo Apps",
    )

    assert len(results) == 1
    repo_path = repos_root / "order-accelerator"
    assert (repo_path / ".git").exists()
    assert (repo_path / "demo_manifest.json").exists()
    manifest = json.loads((repo_path / "demo_manifest.json").read_text(encoding="utf-8"))
    assert manifest["sandbox_space_name"] == "TryCelonis Demo Apps"
    inventory = json.loads((repos_root / "sandbox-space-inventory.json").read_text(encoding="utf-8"))
    assert inventory["space_name"] == "TryCelonis Demo Apps"

    branch = subprocess.run(
        ["git", "branch", "--show-current"],
        cwd=str(repo_path),
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    assert branch == "main"


@pytest.mark.skipif(shutil.which("git") is None, reason="git is required")
def test_create_variant_branch_updates_registry(tmp_path: Path) -> None:
    catalog = DemoCatalog(
        catalog_url="https://trycelonis.example/partners",
        generated_at="2026-03-22T00:00:00+00:00",
        demos=(
            DemoCard(
                name="Claims Recovery Cockpit",
                slug="claims-recovery-cockpit",
                source_url="https://trycelonis.example/demos/claims-recovery",
                summary="A demo cockpit for claims recovery.",
                industries=("automotive",),
                tags=("dashboard",),
                confidence=0.8,
            ),
        ),
    )
    repos_root = tmp_path / "demo-repos"
    bootstrap_demo_repos(
        catalog,
        repos_root=repos_root,
        sandbox_space_name="TryCelonis Demo Apps",
    )

    repo_path = repos_root / "claims-recovery-cockpit"
    branch_name = create_variant_branch(
        repo_path,
        industry="Automotive",
        client_name="Contoso",
    )

    assert branch_name == "client/automotive-contoso"
    registry = json.loads((repo_path / "variants" / "registry.json").read_text(encoding="utf-8"))
    assert registry["variants"][0]["branch"] == branch_name