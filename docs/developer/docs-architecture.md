# Documentation Architecture

This project now uses MkDocs Material as the primary documentation authoring system.

## Source and Build

- Docs source: `docs/`
- Config: `mkdocs.yml`
- Built output: `docs_site/`
- In-app mount path: `/docs-site`

## Legacy Paths

Legacy endpoints under `/docu/*.html` are redirected to `/docs-site/*` to preserve bookmarks.

## Packaging

- Docker includes `docs_site/` in runtime image.
- Desktop packaging includes `docs_site/` in bundled data.
