from __future__ import annotations

import json
import re
import subprocess
from dataclasses import asdict, dataclass
from datetime import datetime, UTC
from html.parser import HTMLParser
from pathlib import Path
from typing import Callable
from urllib.parse import urljoin, urlparse

import httpx
from sqlmodel import Session, select

from foundry.models import TryCelonisDemo


KNOWN_INDUSTRIES: tuple[str, ...] = (
    "automotive",
    "consumer goods",
    "energy",
    "financial services",
    "healthcare",
    "life sciences",
    "manufacturing",
    "mining",
    "pharma",
    "retail",
    "telecommunications",
    "utilities",
)

COMMON_NAV_LABELS = {
    "about",
    "blog",
    "book a demo",
    "careers",
    "contact",
    "cookie settings",
    "docs",
    "events",
    "home",
    "learn more",
    "login",
    "partners",
    "pricing",
    "privacy",
    "resources",
    "sign in",
    "support",
    "terms",
}

TAG_KEYWORDS: dict[str, tuple[str, ...]] = {
    "action-flow": ("action flow", "workflow", "automation"),
    "dashboard": ("dashboard", "cockpit", "analytics"),
    "execution-app": ("app", "workspace", "execution"),
    "kpi": ("kpi", "metric", "score"),
    "object-centric": ("ocpm", "object-centric"),
    "process-mining": ("process mining", "variant", "throughput time"),
}


@dataclass(frozen=True)
class DemoSourceEvidence:
    page_url: str
    title: str
    summary: str
    image_urls: tuple[str, ...] = ()


@dataclass(frozen=True)
class DemoCard:
    name: str
    slug: str
    source_url: str
    summary: str
    industries: tuple[str, ...] = ()
    tags: tuple[str, ...] = ()
    image_urls: tuple[str, ...] = ()
    evidence: tuple[DemoSourceEvidence, ...] = ()
    confidence: float = 0.0


@dataclass(frozen=True)
class DemoCatalog:
    catalog_url: str
    generated_at: str
    demos: tuple[DemoCard, ...]


@dataclass(frozen=True)
class BootstrapResult:
    demo_slug: str
    repo_path: Path
    sandbox_manifest_path: Path
    branch: str


@dataclass(frozen=True)
class TryCelonisSyncResult:
    source_kind: str
    catalog_url: str
    imported: int
    updated: int
    total: int


class _SimpleHtmlPageParser(HTMLParser):
    def __init__(self, page_url: str) -> None:
        super().__init__(convert_charrefs=True)
        self.page_url = page_url
        self._text_parts: list[str] = []
        self._headings: list[str] = []
        self._paragraphs: list[str] = []
        self._anchors: list[dict[str, str]] = []
        self._images: list[str] = []
        self._title_parts: list[str] = []
        self._current_anchor_href = ""
        self._current_anchor_text: list[str] = []
        self._current_context: str | None = None
        self._current_text_parts: list[str] = []

    @property
    def title(self) -> str:
        return _normalize_whitespace(" ".join(self._title_parts))

    @property
    def headings(self) -> tuple[str, ...]:
        return tuple(self._headings)

    @property
    def paragraphs(self) -> tuple[str, ...]:
        return tuple(self._paragraphs)

    @property
    def anchors(self) -> tuple[dict[str, str], ...]:
        return tuple(self._anchors)

    @property
    def images(self) -> tuple[str, ...]:
        return tuple(self._images)

    @property
    def visible_text(self) -> str:
        return _normalize_whitespace(" ".join(self._text_parts))

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = {key: value or "" for key, value in attrs}
        if tag == "a":
            self._current_anchor_href = attributes.get("href", "")
            self._current_anchor_text = []
        elif tag == "img":
            src = attributes.get("src", "").strip()
            if src:
                self._images.append(urljoin(self.page_url, src))
        elif tag in {"title", "p", "h1", "h2", "h3", "li"}:
            self._current_context = tag
            self._current_text_parts = []

    def handle_endtag(self, tag: str) -> None:
        if tag == "a":
            text = _normalize_whitespace(" ".join(self._current_anchor_text))
            href = self._current_anchor_href.strip()
            if href and text:
                self._anchors.append({"href": urljoin(self.page_url, href), "text": text})
            self._current_anchor_href = ""
            self._current_anchor_text = []
            return

        if self._current_context == tag:
            text = _normalize_whitespace(" ".join(self._current_text_parts))
            if text:
                self._text_parts.append(text)
                if tag == "title":
                    self._title_parts.append(text)
                elif tag in {"h1", "h2", "h3"}:
                    self._headings.append(text)
                elif tag == "p":
                    self._paragraphs.append(text)
            self._current_context = None
            self._current_text_parts = []

    def handle_data(self, data: str) -> None:
        text = _normalize_whitespace(data)
        if not text:
            return
        if self._current_anchor_href:
            self._current_anchor_text.append(text)
        if self._current_context:
            self._current_text_parts.append(text)


def _normalize_whitespace(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "demo-app"


def _same_host(left: str, right: str) -> bool:
    return urlparse(left).netloc.lower() == urlparse(right).netloc.lower()


def _looks_like_demo_url(url: str) -> bool:
    parsed = urlparse(url)
    tokens = {token for token in parsed.path.lower().split("/") if token}
    if not tokens:
        return False
    if {"app", "apps", "demo", "demos", "solution", "solutions"}.intersection(tokens):
        return True
    return parsed.path.count("/") >= 2


def _looks_like_demo_anchor(text: str, href: str) -> bool:
    normalized = text.strip().lower()
    if not normalized or normalized in COMMON_NAV_LABELS:
        return False
    if len(normalized) < 6:
        return False
    if normalized in {"read more", "details", "view more", "watch now"}:
        return False
    return _looks_like_demo_url(href)


def _infer_industries(text: str) -> tuple[str, ...]:
    lower_text = text.lower()
    return tuple(industry for industry in KNOWN_INDUSTRIES if industry in lower_text)


def _infer_tags(text: str) -> tuple[str, ...]:
    lower_text = text.lower()
    tags = [tag for tag, keywords in TAG_KEYWORDS.items() if any(keyword in lower_text for keyword in keywords)]
    return tuple(sorted(tags))


def _page_confidence(url: str, page: _SimpleHtmlPageParser) -> float:
    score = 0.0
    if _looks_like_demo_url(url):
        score += 0.35
    if page.headings:
        score += 0.2
    if page.paragraphs:
        score += 0.15
    if page.images:
        score += 0.1
    if _infer_industries(page.visible_text):
        score += 0.1
    if _infer_tags(page.visible_text):
        score += 0.1
    return min(score, 1.0)


def _choose_name(page: _SimpleHtmlPageParser, fallback: str) -> str:
    candidates = [*page.headings, page.title, fallback]
    for candidate in candidates:
        cleaned = _normalize_whitespace(candidate)
        if len(cleaned) >= 5:
            return re.sub(r"\s+[\-|:]\s+.*$", "", cleaned).strip()
    return fallback


def _choose_summary(page: _SimpleHtmlPageParser) -> str:
    for paragraph in page.paragraphs:
        normalized = _normalize_whitespace(paragraph)
        if len(normalized) >= 40:
            return normalized
    return _normalize_whitespace(page.visible_text)[:240].strip()


def _fetch_html(url: str, timeout_seconds: float = 20.0) -> str:
    with httpx.Client(follow_redirects=True, timeout=timeout_seconds) as client:
        response = client.get(url)
        response.raise_for_status()
        return response.text


def crawl_demo_catalog(
    catalog_url: str,
    *,
    max_pages: int = 40,
    fetch_html: Callable[[str], str] | None = None,
) -> DemoCatalog:
    fetch = fetch_html or _fetch_html
    queue = [catalog_url]
    visited: set[str] = set()
    demos: dict[str, dict[str, object]] = {}

    while queue and len(visited) < max_pages:
        page_url = queue.pop(0)
        if page_url in visited:
            continue
        visited.add(page_url)

        html = fetch(page_url)
        parser = _SimpleHtmlPageParser(page_url)
        parser.feed(html)

        if page_url != catalog_url:
            fallback_name = Path(urlparse(page_url).path).stem.replace("-", " ").title()
            name = _choose_name(parser, fallback_name)
            slug = slugify(name)
            summary = _choose_summary(parser)
            evidence = DemoSourceEvidence(
                page_url=page_url,
                title=parser.title or name,
                summary=summary,
                image_urls=tuple(parser.images[:5]),
            )
            merged = demos.setdefault(
                slug,
                {
                    "name": name,
                    "slug": slug,
                    "source_url": page_url,
                    "summary": summary,
                    "industries": set(),
                    "tags": set(),
                    "image_urls": [],
                    "evidence": [],
                    "confidence": 0.0,
                },
            )
            merged["industries"].update(_infer_industries(parser.visible_text))
            merged["tags"].update(_infer_tags(parser.visible_text))
            merged["image_urls"] = list(dict.fromkeys([*merged["image_urls"], *parser.images]))[:8]
            merged["evidence"].append(evidence)
            merged["confidence"] = max(float(merged["confidence"]), _page_confidence(page_url, parser))
            if len(summary) > len(str(merged["summary"])):
                merged["summary"] = summary
            if len(name) > len(str(merged["name"])):
                merged["name"] = name

        for anchor in parser.anchors:
            href = anchor["href"]
            text = anchor["text"]
            if not _same_host(catalog_url, href):
                continue
            if href in visited or href in queue:
                continue
            if _looks_like_demo_anchor(text, href):
                queue.append(href)

    demo_rows = tuple(
        DemoCard(
            name=str(row["name"]),
            slug=str(row["slug"]),
            source_url=str(row["source_url"]),
            summary=str(row["summary"]),
            industries=tuple(sorted(row["industries"])),
            tags=tuple(sorted(row["tags"])),
            image_urls=tuple(row["image_urls"]),
            evidence=tuple(row["evidence"]),
            confidence=float(row["confidence"]),
        )
        for row in sorted(demos.values(), key=lambda item: str(item["name"]).lower())
    )
    return DemoCatalog(
        catalog_url=catalog_url,
        generated_at=datetime.now(UTC).isoformat(),
        demos=demo_rows,
    )


def catalog_to_json(catalog: DemoCatalog) -> str:
    return json.dumps(asdict(catalog), indent=2)


def save_catalog(catalog: DemoCatalog, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(catalog_to_json(catalog), encoding="utf-8")


def load_catalog(path: Path) -> DemoCatalog:
    payload = json.loads(path.read_text(encoding="utf-8"))
    demos = []
    for row in payload.get("demos", []):
        evidence = tuple(
            DemoSourceEvidence(
                page_url=item["page_url"],
                title=item["title"],
                summary=item["summary"],
                image_urls=tuple(item.get("image_urls", [])),
            )
            for item in row.get("evidence", [])
        )
        demos.append(
            DemoCard(
                name=row["name"],
                slug=row["slug"],
                source_url=row["source_url"],
                summary=row.get("summary", ""),
                industries=tuple(row.get("industries", [])),
                tags=tuple(row.get("tags", [])),
                image_urls=tuple(row.get("image_urls", [])),
                evidence=evidence,
                confidence=float(row.get("confidence", 0.0)),
            )
        )
    return DemoCatalog(
        catalog_url=payload["catalog_url"],
        generated_at=payload["generated_at"],
        demos=tuple(demos),
    )


def sync_catalog_to_database(
    session: Session,
    *,
    organization_id,
    catalog: DemoCatalog,
    source_kind: str,
) -> TryCelonisSyncResult:
    existing_rows = session.exec(
        select(TryCelonisDemo).where(TryCelonisDemo.organization_id == organization_id)
    ).all()
    existing_by_slug = {row.slug: row for row in existing_rows}

    imported = 0
    updated = 0
    now = datetime.now(UTC).replace(tzinfo=None)

    for demo in catalog.demos:
        row = existing_by_slug.get(demo.slug)
        evidence_json = [asdict(item) for item in demo.evidence]
        if row is None:
            row = TryCelonisDemo(
                organization_id=organization_id,
                title=demo.name,
                slug=demo.slug,
                summary=demo.summary,
                source_url=demo.source_url,
                catalog_url=catalog.catalog_url,
                source_kind=source_kind,
                industries_json=list(demo.industries),
                tags_json=list(demo.tags),
                image_urls_json=list(demo.image_urls),
                evidence_json=evidence_json,
                confidence_score=demo.confidence,
                last_synced_at=now,
                created_at=now,
                updated_at=now,
            )
            session.add(row)
            imported += 1
            continue

        row.title = demo.name
        row.summary = demo.summary
        row.source_url = demo.source_url
        row.catalog_url = catalog.catalog_url
        row.source_kind = source_kind
        row.industries_json = list(demo.industries)
        row.tags_json = list(demo.tags)
        row.image_urls_json = list(demo.image_urls)
        row.evidence_json = evidence_json
        row.confidence_score = demo.confidence
        row.is_visible = True
        row.last_synced_at = now
        row.updated_at = now
        session.add(row)
        updated += 1

    session.commit()
    total = len(
        session.exec(select(TryCelonisDemo).where(TryCelonisDemo.organization_id == organization_id)).all()
    )
    return TryCelonisSyncResult(
        source_kind=source_kind,
        catalog_url=catalog.catalog_url,
        imported=imported,
        updated=updated,
        total=total,
    )


def sync_trycelonis_demos(
    session: Session,
    *,
    organization_id,
    catalog_url: str = "",
    manifest_path: str = "",
    fetch_html: Callable[[str], str] | None = None,
) -> TryCelonisSyncResult:
    normalized_manifest = Path(manifest_path).expanduser() if manifest_path.strip() else None
    if normalized_manifest and normalized_manifest.exists():
        catalog = load_catalog(normalized_manifest)
        return sync_catalog_to_database(
            session,
            organization_id=organization_id,
            catalog=catalog,
            source_kind="manifest",
        )

    normalized_url = catalog_url.strip()
    if not normalized_url:
        raise ValueError("No TryCelonis catalog source configured. Set a catalog URL or manifest path.")

    catalog = crawl_demo_catalog(normalized_url, fetch_html=fetch_html)
    if not catalog.demos:
        raise ValueError(
            "No TryCelonis demos were discovered. The configured catalog may require login; provide a manifest path for curated imports."
        )
    return sync_catalog_to_database(
        session,
        organization_id=organization_id,
        catalog=catalog,
        source_kind="catalog",
    )


def render_space_inventory(catalog: DemoCatalog, space_name: str, repos_root: Path) -> dict[str, object]:
    return {
        "space_name": space_name,
        "managed_by": "celonis-delivery-forge",
        "generated_at": datetime.now(UTC).isoformat(),
        "apps": [
            {
                "name": demo.name,
                "slug": demo.slug,
                "repo_path": str((repos_root / demo.slug).resolve()),
                "default_branch": "main",
                "lifecycle": {
                    "desired_state": "stopped",
                    "spin_up_strategy": "deploy-on-demand",
                    "spin_down_strategy": "remove-package-or-disable-space-assets",
                },
                "source_url": demo.source_url,
                "industries": list(demo.industries),
                "tags": list(demo.tags),
            }
            for demo in catalog.demos
        ],
    }


def _run_git(args: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        check=True,
    )


def _git_branch_exists(repo_path: Path, branch_name: str) -> bool:
    result = subprocess.run(
        ["git", "rev-parse", "--verify", branch_name],
        cwd=str(repo_path),
        capture_output=True,
        text=True,
        check=False,
    )
    return result.returncode == 0


def _ensure_git_repo(repo_path: Path, branch_name: str, commit_message: str) -> None:
    if (repo_path / ".git").exists():
        return
    try:
        _run_git(["init", "-b", branch_name], cwd=repo_path)
    except subprocess.CalledProcessError:
        _run_git(["init"], cwd=repo_path)
        _run_git(["checkout", "-B", branch_name], cwd=repo_path)
    _run_git(["config", "user.name", "Celonis Delivery Forge"], cwd=repo_path)
    _run_git(["config", "user.email", "forge@example.invalid"], cwd=repo_path)
    _run_git(["add", "."], cwd=repo_path)
    _run_git(["commit", "-m", commit_message], cwd=repo_path)


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _repo_readme(demo: DemoCard, sandbox_space_name: str) -> str:
    industries = ", ".join(demo.industries) if demo.industries else "TBD"
    tags = ", ".join(demo.tags) if demo.tags else "TBD"
    return (
        f"# {demo.name}\n\n"
        f"This repository contains the reconstructed implementation plan for the TryCelonis demo app `{demo.slug}`.\n\n"
        f"## Source\n\n"
        f"- Catalog page: {demo.source_url}\n"
        f"- Confidence: {demo.confidence:.2f}\n"
        f"- Industries detected: {industries}\n"
        f"- Tags detected: {tags}\n\n"
        f"## Sandbox Tenant\n\n"
        f"- Target space: {sandbox_space_name}\n"
        f"- Default branch: `main`\n"
        f"- Client and industry variants: create dedicated branches via the Forge demo CLI.\n\n"
        f"## Rebuild Scope\n\n"
        f"{demo.summary}\n"
    )


def _variant_manifest(branch_name: str, client_name: str, industry: str) -> dict[str, object]:
    return {
        "branch": branch_name,
        "client_name": client_name,
        "industry": industry,
        "created_at": datetime.now(UTC).isoformat(),
        "dummy_data_profile": slugify(industry or client_name or branch_name),
    }


def bootstrap_demo_repos(
    catalog: DemoCatalog,
    *,
    repos_root: Path,
    sandbox_space_name: str,
    default_branch: str = "main",
    create_initial_commit: bool = True,
) -> list[BootstrapResult]:
    repos_root.mkdir(parents=True, exist_ok=True)
    results: list[BootstrapResult] = []

    for demo in catalog.demos:
        repo_path = repos_root / demo.slug
        repo_path.mkdir(parents=True, exist_ok=True)

        _write_json(
            repo_path / "demo_manifest.json",
            {
                "name": demo.name,
                "slug": demo.slug,
                "source_url": demo.source_url,
                "summary": demo.summary,
                "industries": list(demo.industries),
                "tags": list(demo.tags),
                "sandbox_space_name": sandbox_space_name,
                "default_branch": default_branch,
                "confidence": demo.confidence,
                "evidence": [asdict(item) for item in demo.evidence],
            },
        )
        _write_json(
            repo_path / "sandbox" / "deployment.json",
            {
                "space_name": sandbox_space_name,
                "package_name": demo.name,
                "package_key": demo.slug,
                "spin_up": {
                    "mode": "on-demand",
                    "notes": "Deploy or refresh the demo package before client meetings.",
                },
                "spin_down": {
                    "mode": "manual",
                    "notes": "Remove or disable the deployed package when the demo is no longer needed.",
                },
            },
        )
        _write_json(
            repo_path / "variants" / "registry.json",
            {
                "default_branch": default_branch,
                "variants": [],
            },
        )
        (repo_path / ".gitignore").write_text(".DS_Store\nThumbs.db\n", encoding="utf-8")
        (repo_path / "README.md").write_text(_repo_readme(demo, sandbox_space_name), encoding="utf-8")
        (repo_path / "rebuild_notes.md").write_text(
            "# Rebuild Notes\n\n"
            "Document assumptions, Celonis assets to recreate, data requirements, and open gaps here.\n",
            encoding="utf-8",
        )

        if create_initial_commit:
            _ensure_git_repo(repo_path, default_branch, f"Bootstrap {demo.slug} demo repo")

        results.append(
            BootstrapResult(
                demo_slug=demo.slug,
                repo_path=repo_path,
                sandbox_manifest_path=repo_path / "sandbox" / "deployment.json",
                branch=default_branch,
            )
        )

    _write_json(repos_root / "sandbox-space-inventory.json", render_space_inventory(catalog, sandbox_space_name, repos_root))
    return results


def create_variant_branch(
    repo_path: Path,
    *,
    industry: str,
    client_name: str,
    from_branch: str = "main",
) -> str:
    branch_slug = slugify(f"{industry}-{client_name}")
    branch_name = f"client/{branch_slug}"
    if not (repo_path / ".git").exists():
        raise ValueError(f"Not a git repository: {repo_path}")

    _run_git(["checkout", from_branch], cwd=repo_path)
    if _git_branch_exists(repo_path, branch_name):
        _run_git(["checkout", branch_name], cwd=repo_path)
    else:
        _run_git(["checkout", "-b", branch_name, from_branch], cwd=repo_path)

    registry_path = repo_path / "variants" / "registry.json"
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    variants = list(registry.get("variants", []))
    variant_payload = _variant_manifest(branch_name, client_name, industry)
    if not any(row.get("branch") == branch_name for row in variants):
        variants.append(variant_payload)
    registry["variants"] = sorted(variants, key=lambda row: row["branch"])
    _write_json(registry_path, registry)
    _write_json(repo_path / "variants" / f"{slugify(branch_name)}.json", variant_payload)
    return branch_name