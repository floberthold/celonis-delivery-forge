# User Route Reference

This reference maps primary UI routes to purpose.

## Authentication and Account

- `/login` - sign in.
- `/register` - self-service account registration.
- `/register/verify?token=...` - email verification endpoint.
- `/forgot-password` - request reset link.
- `/reset-password?token=...` - set new password.
- `/account-ui` - profile and password updates.

## Core Delivery

- `/dashboard` - command center.
- `/clients-ui` - clients and tenant metadata.
- `/projects-ui` - projects and project-level management.
- `/assets-ui` - delivery assets.
- `/reviews-ui` - governed review flow.
- `/people-ui` - people and role maintenance.
- `/todos-ui` - task execution board/list.
- `/files-ui` - file registry and upload area.
- `/timeline-ui` - audit timeline.

## Orchestration and KPI

- `/orchestration-ui` - orchestration board and assignments.
- `/kpis-ui` - KPI editor and version lifecycle.
- `/kpi-book-ui/{client_id}` - client KPI view.
- `/snapshots-ui/{client_id}` - client snapshots listing.

## Support and Docs

- `/tenant-ui` - tenant workspace UI.
- `/docs` - OpenAPI docs.
- `/docs-site/` - MkDocs documentation site.
- `/health` - runtime health payload.
