# Account and Security

This page explains account lifecycle and self-service security actions.

## Registration

1. Open `/register`.
2. Enter name, email, password, and confirmation.
3. Submit the form.
4. Check your mailbox for the verification email.

If SMTP is not configured, verification email delivery will fail.

## Email Verification

1. Open the verification email.
2. Click the `/register/verify?token=...` link.
3. Confirm successful redirect back to `/login`.

## Login

1. Open `/login`.
2. Enter verified credentials.
3. Submit and confirm redirect to `/dashboard` or your requested `next_path`.

If the app returns to login repeatedly, use troubleshooting.

## Forgot Password

1. Open `/forgot-password`.
2. Enter your email.
3. Open reset email.
4. Click `/reset-password?token=...`.
5. Set the new password.
6. Sign in again.

## Account Overview

Use `/account-ui` to:

- Change your display name.
- Change your email (if not already used).
- Change your password with confirmation.
- Review your organization memberships.

## Celonis App Key Setup

Use this flow when preflight or snapshots show missing token or permission issues.

### 1. Create the app key in Celonis

1. Open your Celonis tenant admin area for API/application keys.
2. Create a new app key for Foundry usage.
3. Assign service permissions for the APIs that Foundry calls.
4. Copy the token value securely.

### 2. Required rights matrix (minimum)

Foundry features map to these endpoint families and required Celonis rights:

| Foundry feature | Celonis endpoint families | Minimum app-key rights |
| --- | --- | --- |
| Preflight: core | `/` | Core platform/API access |
| Preflight + snapshots: process mining | `/process-mining/api/teams`, `/process-mining/api/data-models` | Process Mining read rights |
| Preflight + snapshots: data integration | `/integration/api/pools`, `/integration/api/v1/pools`, `/integration/api/v1/jobs`, `/integration/api/jobs`, `/integration/api/v1/transformations` | Data Integration read rights for pools, jobs, transformations |
| Preflight + snapshots: studio and package inventory | `/studio/api/spaces`, `/package-manager/api/spaces`, `/package-manager/api/packages`, `/package-manager/api/packages/{package_key}/assets` | Studio + Package Manager read rights |
| Preflight + snapshots: apps | `/apps/api/packages`, `/apps/api/apps` | Apps read rights |
| Snapshot enrichment: knowledge models | `/knowledge-model/api/knowledge-models`, `/semantic-layer/api/knowledge-models` | Knowledge Model/Semantic Layer read rights |

Recommended: grant all read scopes above for full snapshot coverage.

Important: package-level permissions (Use/Edit/Delete/Manage on a specific Studio package)
do not always grant tenant-wide API listing endpoints such as `/studio/api/spaces` or
`/package-manager/api/packages`. If preflight shows `redirect-to-login` for Studio while
package permissions look complete, request service-level Studio/Package Manager API read
rights for the app key.

### 3. Configure the token in Foundry

Preferred (per-user):

1. Open `/onboarding/celonis-setup`.
2. Step 1: Select or create client.
3. Step 2: Save active tenant base URL connection.
4. Step 3: Paste the app key token and save.
5. Step 4: Run preflight.

Fallback (system-wide): set `FORGE_CELONIS_API_TOKEN` in environment configuration.

### 4. Validate and interpret preflight

- `authorized`: service is ready.
- `redirect-to-login`, `forbidden`, `unauthorized`: token is present but missing service scope or blocked by policy.
- `missing-token`: no personal token and no system token fallback.
- `unreachable`: tenant URL/network issue.

If setup reports limited scope, snapshots can still run but will return partial coverage for unauthorized services.

### 5. Snapshot run checklist

1. Open `/snapshots-ui/{client_id}`.
2. Trigger a snapshot.
3. Inspect detail + coverage report:
	- `/snapshots-ui/{client_id}/{snapshot_id}/detail`
	- `/snapshots-ui/{client_id}/{snapshot_id}/coverage`

If coverage shows permission-limited families, expand app-key rights for corresponding endpoint families above.

## Security Practices

- Use unique passwords.
- Rotate passwords for shared test environments.
- Sign out when done on shared machines.
- Ask an org owner to verify your role if access is missing.

## Validation Checklist

- `/account-ui` loads successfully after login.
- Name/email updates persist after page refresh.
- Password update allows next login with new password.
- Old password no longer works.
