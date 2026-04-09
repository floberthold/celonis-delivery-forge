# Incident Playbooks

Use this page for rapid diagnosis and recovery.

## Incident: Login Loop

Symptoms:

- User signs in, then returns to `/login`.

Actions:

1. Check `/health` database mode.
2. Confirm active runtime process and DB target are expected.
3. Verify user organization membership exists.
4. Clear browser cookies or test in private window.
5. Re-test login.

## Incident: Invalid Credentials for Known User

Actions:

1. Confirm user exists in active database.
2. Confirm runtime is not using a different fallback DB than expected.
3. Reset password via `/forgot-password`.
4. Re-test login.

## Incident: Registration/Reset Email Not Arriving

Actions:

1. Verify SMTP env vars are set.
2. Verify provider auth details and sender permissions.
3. Verify `FORGE_PUBLIC_BASE_URL` is correct.
4. Trigger flow again and inspect server logs.

## Incident: Startup Falls Back Unexpectedly

Actions:

1. Inspect `/health` for `database_startup_mode`.
2. Verify configured DB reachability.
3. Decide whether fallback is acceptable for current environment.
4. For strict mode, set `FORGE_DATABASE_FALLBACK_TO_LOCAL=false` and restart.

## Incident: Integration Failures (Celonis/GitLab)

Actions:

1. Re-check token validity and scopes.
2. Re-check tenant/base URLs.
3. Re-run dashboard/preflight checks.
4. Validate network connectivity from host.

## Incident: Internal Server Error on UI Action

Actions:

1. Reproduce once with clear route/action notes.
2. Capture stack trace from active server logs.
3. Confirm app version and runtime mode.
4. Validate the same flow with a clean test account.
5. Open targeted fix with route-level regression test.
