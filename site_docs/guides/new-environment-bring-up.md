# New Environment Bring-up

This scenario guide takes an admin from empty environment to fully usable setup.

## Goal

Achieve a state where:

- Login and account lifecycle work.
- Core workspaces are usable.
- SMTP-based verification/reset works.
- Basic integrations are configured.

## Step 1: Configure Base Environment

1. Copy `.env.example` to `.env`.
2. Set at least:
   - `FORGE_ENV`
   - `FORGE_JWT_SECRET`
   - `FORGE_PUBLIC_BASE_URL`
   - DB settings

## Step 2: Configure SMTP

Set SMTP variables and validate sender credentials with your provider.

## Step 3: Start Runtime

1. Start app (`uvicorn` or selected runtime mode).
2. Open `/health`.
3. Confirm expected backend and startup mode.

## Step 4: Bootstrap Accounts

1. Register first admin-capable account.
2. Verify email-based activation.
3. Sign in and open `/people-ui`.
4. Create/add additional team users.

## Step 5: Bootstrap Work Context

1. Create client.
2. Create project.
3. Assign project members.
4. Create sample asset and todo.

## Step 6: Verify Governance and Audit

1. Submit a review in `/reviews-ui`.
2. Approve/request changes from a different user.
3. Confirm actions in `/timeline-ui`.

## Step 7: Verify Integrations

1. Configure Celonis token and connection.
2. Run preflight from dashboard.
3. Validate expected response and logs.

## Exit Criteria

- Account lifecycle works.
- Admin can provision users.
- Core workspaces load and persist changes.
- Governance flow works with at least two users.
