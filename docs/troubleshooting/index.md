# Troubleshooting

## Authentication

- Redirect to login repeatedly: check cookie, token expiry, and active organization membership.
- No reset/verification email: verify SMTP variables and sender credentials.

## Startup

- DB timeout errors: verify database reachability and fallback settings.
- Wrong backend in use: inspect `/health` output.

## Integrations

- Celonis preflight failures: verify token and tenant URL.
- GitLab sync failures: verify base URL, token scope, and repository permissions.
