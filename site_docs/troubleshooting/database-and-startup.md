# Database and Startup Issues

Use this page when startup mode or data persistence behaves unexpectedly.

## Problem: Startup Falls Back to Local Unexpectedly

Checks:

1. Inspect `/health` for `database_startup_mode`.
2. Verify configured database reachability.
3. Verify `FORGE_DATABASE_CONNECT_TIMEOUT_SECONDS` is appropriate.
4. Decide if fallback should be disabled for this environment.

## Problem: Data Appears Missing Between Runs

Likely cause:

- Runtime switched between primary DB and fallback DB.

Checks:

1. Confirm active DB mode in `/health`.
2. Confirm where account/entity records were created.
3. Ensure one consistent database target for the environment.

## Problem: Migration/Schema Errors

Checks:

1. Confirm migration scripts are applied.
2. Confirm model/schema changes match migration output.
3. Restart and re-run targeted tests.
4. For sqlite legacy DBs, verify startup repair path executed.

## Problem: Docker DB Startup Failure

Checks:

1. Verify database container status.
2. Verify compose networking and credentials.
3. Retry startup after DB is healthy.
