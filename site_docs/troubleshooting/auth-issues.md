# Authentication Issues

Use this page for sign-in, token, and session errors.

## Problem: Invalid Credentials

Checks:

1. Confirm email/password are correct.
2. Confirm account exists in active runtime database.
3. Confirm password was reset in the same active database context.
4. Retry in private window to bypass stale session state.

## Problem: Login Redirect Loop

Checks:

1. Open `/health` and confirm backend/startup mode.
2. Confirm the app process is the expected one.
3. Confirm user has organization membership.
4. Clear cookies and retry login.

## Problem: Verified User Cannot Access Pages

Checks:

1. Confirm role/membership in `/people-ui`.
2. Confirm org-scoped access for target project/client.
3. Re-authenticate and retry.

## Problem: Password Reset Link Fails

Checks:

1. Confirm token has not expired.
2. Request a new reset link.
3. Confirm `FORGE_PUBLIC_BASE_URL` is correct.
4. Confirm SMTP sender and link delivery are healthy.
