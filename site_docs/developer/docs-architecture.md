# Documentation Architecture

This project now uses MkDocs Material as the primary documentation authoring system.

## Source and Build

- Docs source: `site_docs/`
- Config: `mkdocs.yml`
- Built output: `docs_site/`
- In-app mount path: `/docs-site`

Build command:

```powershell
.\.venv\Scripts\python.exe -m mkdocs build --strict
```

## Legacy Paths

Legacy endpoints under `/docu/*.html` are redirected to `/docs-site/*` to preserve bookmarks.

## Authoring Rules

1. Keep user/admin/developer content separated by audience.
2. Include operational verification steps for new procedures.
3. Update navigation when adding permanent sections.
4. Avoid conflicting instructions across pages.
5. Treat strict build failures as blockers.

## Maintenance Workflow

1. Update markdown in `site_docs/`.
2. Run strict build.
3. Run docs route regression tests.
4. Review generated output in `docs_site/`.
5. Commit source and generated docs changes together.

## Packaging

- Docker includes `docs_site/` in runtime image.
- Desktop packaging includes `docs_site/` in bundled data.
