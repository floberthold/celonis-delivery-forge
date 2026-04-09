# Core Workspaces

This page maps major UI pages to user outcomes.

## Dashboard (`/dashboard`)

Use as the main command center for quick creation and integration actions.

Typical actions:

- Create organization/client/project.
- Trigger Celonis connect/preflight/extract/import forms.
- Navigate to key workspaces.

## Clients (`/clients-ui`)

Use to manage customer/tenant records.

Typical actions:

- Create and update client metadata.
- Maintain Celonis tenant URL references.
- Open client overview details.

## Projects (`/projects-ui`)

Use to manage implementation projects and team membership context.

Typical actions:

- Create projects under clients.
- Maintain project status.
- Open project overview.

## Assets (`/assets-ui`)

Use to register delivery artifacts and track lifecycle status.

Typical actions:

- Create/edit/delete assets.
- Assign metadata and references.
- Link to Celonis artifacts where needed.

Action-flow template library:

- Reusable action-flow templates are stored in `developer/action_flow_templates/`.
- Treat flow templates as `action_flow` assets during rollout.
- Use paired playbooks to validate before using templates in client work.

## People (`/people-ui`)

Use to manage organization members.

Typical actions:

- Add users to your organization.
- Set global role values.
- Update user profile metadata.

## Todos (`/todos-ui`)

Use for operational task tracking.

Typical actions:

- Create and update todo state.
- Track status progression.
- Capture task-level context.

## Files (`/files-ui`)

Use for uploaded or linked delivery files.

Typical actions:

- Upload files.
- Link external resources.
- Browse artifacts by context.

## Timeline (`/timeline-ui`)

Use as an audit and history view.

Typical actions:

- Inspect who changed what.
- Trace entity-level event chronology.
- Support governance reviews.

## Orchestration (`/orchestration-ui`)

Use for governed rollout of action-flow templates.

Typical actions:

- Pick a starter template and set required inputs.
- Run a sandbox validation and capture evidence.
- Submit run for human review before promoting high-risk flows.
