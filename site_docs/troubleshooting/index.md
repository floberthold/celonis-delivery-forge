# Troubleshooting

Use the detailed pages below to diagnose by symptom:

- [Authentication Issues](auth-issues.md)
- [Database and Startup](database-and-startup.md)
- [Integrations and Email](integrations-and-email.md)

## Fast Triage Sequence

1. Check `/health` for backend and startup mode.
2. Confirm runtime mode and active server process.
3. Reproduce once and capture exact route + error.
4. Follow the matching troubleshooting playbook.

## Escalation Data to Capture

- Runtime mode (`uvicorn`, desktop, docker, standalone).
- `/health` payload.
- Route and action that failed.
- Exact error text and stack trace (if available).
