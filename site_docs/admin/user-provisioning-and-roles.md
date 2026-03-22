# User Provisioning and Roles

This page defines how admins create users and maintain access safely.

## Provisioning Paths

## Self-Service Registration

1. User opens `/register`.
2. User verifies via email link.
3. User signs in at `/login`.
4. Admin confirms org membership and role in `/people-ui`.

## Admin-Created Accounts

1. Admin opens `/people-ui`.
2. Creates account with required profile data.
3. Assigns appropriate role and organization context.
4. User signs in and completes profile in `/account-ui`.

## Role Considerations

Global role and organization role both affect capabilities.

Minimum governance model:

- Keep at least two active members for governed projects.
- Separate reviewer and author responsibilities.
- Review role assignments periodically.

## Operational Checks

- Can user sign in successfully?
- Does user appear in `/people-ui`?
- Can user access expected project/client pages?
- Is account self-service update working in `/account-ui`?

## Common Access Issues

- Login works but no data: missing organization membership.
- Repeated redirects to login: stale cookie/session or missing org context.
- Cannot create/update entities: role or membership not sufficient.
