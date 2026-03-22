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
