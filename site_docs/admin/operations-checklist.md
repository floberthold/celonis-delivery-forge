# Operations Checklist

Run this checklist after startup and daily in active environments.

## Startup Checklist

1. Start app in selected runtime mode.
2. Open `/health` and validate:
   - `status` is `ok`
   - `database_backend` is expected
   - `database_startup_mode` is expected
3. Open `/docs-site/` and verify docs are served.
4. Open `/login` and complete one successful sign-in.

## Daily Functional Checks

1. Account flows:
   - Verify `/register` and `/forgot-password` are reachable.
   - Trigger a controlled password reset.
2. Core workspaces:
   - Open `/dashboard`, `/people-ui`, `/projects-ui`, `/reviews-ui`.
3. Integrations:
   - Trigger Celonis preflight from dashboard.
   - Validate GitLab connectivity if configured.
4. Audit:
   - Confirm `/timeline-ui` receives new actions.

## Weekly Governance Checks

1. Ensure governed projects have sufficient active members.
2. Ensure open reviews are being processed.
3. Verify no critical tasks are stuck in stale states.
4. Verify uploads storage growth and retention.

## Change Window Checklist

Before upgrades/config changes:

1. Backup database.
2. Capture current `.env` values securely.
3. Announce maintenance window.
4. Apply change and restart.
5. Re-run startup and daily checks.
