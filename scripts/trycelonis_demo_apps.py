from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "src"))

from foundry.services.trycelonis_demo_rebuild import (
    bootstrap_demo_repos,
    catalog_to_json,
    crawl_demo_catalog,
    create_variant_branch,
    load_catalog,
    render_space_inventory,
    save_catalog,
)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Discover and scaffold TryCelonis demo rebuild repositories.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    discover = subparsers.add_parser("discover", help="Crawl a TryCelonis catalog and write a demo manifest.")
    discover.add_argument("catalog_url")
    discover.add_argument("--output", required=True)
    discover.add_argument("--max-pages", type=int, default=40)

    bootstrap = subparsers.add_parser("bootstrap", help="Create one git repository per discovered demo app.")
    bootstrap.add_argument("--catalog", required=True)
    bootstrap.add_argument("--repos-root", required=True)
    bootstrap.add_argument("--sandbox-space-name", required=True)
    bootstrap.add_argument("--default-branch", default="main")
    bootstrap.add_argument("--no-initial-commit", action="store_true")

    variant = subparsers.add_parser("create-variant", help="Create a client and industry specific branch inside a demo repo.")
    variant.add_argument("--repo", required=True)
    variant.add_argument("--industry", required=True)
    variant.add_argument("--client", required=True)
    variant.add_argument("--from-branch", default="main")

    space = subparsers.add_parser("render-space", help="Render the sandbox space inventory from a catalog.")
    space.add_argument("--catalog", required=True)
    space.add_argument("--repos-root", required=True)
    space.add_argument("--space-name", required=True)
    space.add_argument("--output", required=True)
    return parser


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()

    if args.command == "discover":
        catalog = crawl_demo_catalog(args.catalog_url, max_pages=args.max_pages)
        output = Path(args.output)
        save_catalog(catalog, output)
        print(f"discovered_demos={len(catalog.demos)} output={output}")
        return

    if args.command == "bootstrap":
        catalog = load_catalog(Path(args.catalog))
        results = bootstrap_demo_repos(
            catalog,
            repos_root=Path(args.repos_root),
            sandbox_space_name=args.sandbox_space_name,
            default_branch=args.default_branch,
            create_initial_commit=not args.no_initial_commit,
        )
        print(f"bootstrapped_repos={len(results)} repos_root={Path(args.repos_root)}")
        return

    if args.command == "create-variant":
        branch_name = create_variant_branch(
            Path(args.repo),
            industry=args.industry,
            client_name=args.client,
            from_branch=args.from_branch,
        )
        print(f"created_branch={branch_name} repo={Path(args.repo)}")
        return

    if args.command == "render-space":
        catalog = load_catalog(Path(args.catalog))
        payload = render_space_inventory(catalog, args.space_name, Path(args.repos_root))
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        print(f"rendered_space_inventory={output}")
        return

    parser.error(f"Unsupported command: {args.command}")


if __name__ == "__main__":
    main()