# Account Lifecycle Flows

## Register

1. Open `/register`.
2. Submit name, email, password, and confirmation.
3. Confirm success banner indicating verification email was sent.

## Verify Email

1. Open verification email.
2. Click activation link.
3. Confirm redirect to login with account activation success.

## Login

1. Open `/login`.
2. Sign in with verified account credentials.
3. Confirm redirect to `/dashboard` (or preserved `next_path`).

## Manage My Account

1. Open `/account-ui`.
2. Update name/email.
3. Optionally set new password and confirmation.
4. Save and confirm success banner.

## Forgot Password

1. Open `/forgot-password`.
2. Submit your account email.
3. Open reset email and follow reset link.
4. Set new password and sign in.

## Common Issues

- No email received: verify SMTP env vars and provider sender policies.
- Expired token: request a new reset or verification email.
- Login succeeds but no data: verify organization membership.
