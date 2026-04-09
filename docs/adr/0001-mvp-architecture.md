# ADR 0001: Foundry MVP Architecture

## Status
Accepted

## Context
The MVP must support dual-control (4-eyes) governance for Celonis delivery projects with local execution.

## Decision
- Python-first implementation with FastAPI.
- PostgreSQL as primary persistence from day one.
- Local account authentication with JWT.
- Optional read-only Celonis imports, explicitly user-triggered.
- Desktop-style local app execution via embedded browser wrapper over local backend.

## Consequences
- Team-ready data model and review workflows are available early.
- SSO and deeper Celonis integration can be added later without replacing the core.
- Desktop packaging adds some runtime complexity but keeps UX close to a local app.
