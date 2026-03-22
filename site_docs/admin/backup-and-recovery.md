# Backup and Recovery

Use these procedures to protect operational data and restore service quickly.

## SQLite Backup (Local/Fallback)

1. Stop the application process.
2. Locate active database file:
   - `./foundry.db` or
   - `%LOCALAPPDATA%/CelonisDeliveryForge/foundry-local.db`
3. Copy the file to secure backup storage.
4. Restart the app and verify `/health`.

## Postgres Backup (Docker/Managed)

Recommended minimum:

- Daily logical backup (`pg_dump`).
- Retention policy by environment criticality.
- Restore test at regular intervals.

## Restore Procedure

1. Stop application.
2. Restore database from validated backup.
3. Start application.
4. Run `/health` and key UI smoke checks.
5. Validate recent entities in `/projects-ui`, `/people-ui`, `/timeline-ui`.

## Recovery Verification

After restore, verify:

- Login works for admin account.
- Core routes load.
- Recent activities appear in timeline.
- Registration/reset flows still send email if SMTP is configured.

## Common Recovery Pitfalls

- Restoring wrong DB file while app uses fallback path.
- Restarting with old `.env` values after migration.
- Skipping post-restore functional checks.
