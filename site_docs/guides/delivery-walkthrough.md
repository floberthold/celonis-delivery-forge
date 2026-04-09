# Delivery Walkthrough

Follow this sequence for a complete governed delivery cycle.

## 1. Access and Preconditions

1. Sign in at `/login`.
2. Verify people/project membership in `/people-ui` and `/projects-ui`.
3. Ensure at least two active project members.

## 2. Create Core Artifacts

1. Create client in `/clients-ui`.
2. Create project and memberships in `/projects-ui`.
3. Create asset in `/assets-ui`.

## 3. Run Companion Checks

1. Open `/dashboard`.
2. Save tenant connection for client.
3. Run preflight checks and inspect status badges.
4. Select an action-flow starter template and verify required inputs.

## 4. Execute Delivery Work

1. Track tasks in `/todos-ui`.
2. Upload/link artifacts in `/files-ui`.
3. Manage KPI formulas in `/kpis-ui`.
4. Execute sandbox run for selected action-flow template.
5. Confirm fallback path behavior with one injected failure.

## 5. Review and Audit

1. Submit review in `/reviews-ui`.
2. Ensure author and reviewer are different users.
3. Verify timeline entries in `/timeline-ui`.
4. Verify evidence bundle includes logs, fallback outcome, and reviewer decision.

## 6. Closeout

1. Resolve outstanding reviews.
2. Update project/client health surfaces.
3. Capture reusable knowledge (snapshots/KPI references).
4. Register successful pattern as reusable action-flow asset.
