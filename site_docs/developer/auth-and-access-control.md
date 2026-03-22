# Auth and Access Control

This page documents identity and authorization behavior for API and UI surfaces.

## Authentication Modes

- API: bearer token via `/auth/token`.
- UI: cookie-based session token set at login.

## Token Claims and Selection

`/auth/token` can include selected organization context:

- If account has one org membership, org can be auto-selected.
- If account has multiple org memberships, `organization_id` is required for API login.

## Access Control Building Blocks

- Current actor dependency resolves person and active organization context.
- Route handlers must enforce organization-scoped access.
- Role and membership checks should be explicit in route/service logic.

## UI Login Considerations

- UI pages redirect unauthenticated browser requests to `/login`.
- `next_path` preserves intended destination after sign-in.
- Login loops usually indicate token/session/org-context mismatch.

## Security Notes

- Replace `FORGE_JWT_SECRET` in all real environments.
- Keep JWT expiry aligned to operational needs.
- Use HTTPS and secure cookie settings in production deployments.
- Enforce principle of least privilege for admin roles.
