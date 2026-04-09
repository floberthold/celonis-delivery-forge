# Integrations and Email Issues

Use this page for Celonis, GitLab, and SMTP runtime failures.

## Problem: Celonis Preflight Fails

Checks:

1. Validate `FORGE_CELONIS_API_TOKEN`.
2. Validate tenant/base URL format.
3. Re-run preflight from dashboard.
4. Confirm network connectivity and timeout settings.

## Problem: Celonis Extract/Import Errors

Checks:

1. Confirm connection was saved to correct client.
2. Confirm token has required permissions.
3. Confirm endpoint path and payload validity.
4. Review response details and retry with minimal payload.

## Problem: GitLab Integration Fails

Checks:

1. Validate `FORGE_GITLAB_BASE_URL`.
2. Validate `FORGE_GITLAB_API_TOKEN` scopes.
3. Confirm repository/project permissions.
4. Retry action from relevant UI/API surface.

## Problem: Verification/Reset Email Not Delivered

Checks:

1. Confirm SMTP host/port/credentials.
2. Confirm STARTTLS/SSL mode matches provider.
3. Confirm `FORGE_SMTP_FROM_EMAIL` is authorized.
4. Confirm `FORGE_PUBLIC_BASE_URL` is correct.
5. Trigger flow again and inspect server logs.

## Provider Defaults

- Microsoft 365: host `smtp.office365.com`, port `587`, STARTTLS `true`
- Gmail: host `smtp.gmail.com`, port `587`, STARTTLS `true` with app password
