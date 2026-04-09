# Subscription Event Client Comms Draft

## Outcome
Draft high-quality client updates rapidly with human approval control.

## Source spec
- `../specs/subscription-event-client-comms-draft.json`

## Setup
1. Define severity events that trigger draft generation.
2. Configure audience and tone defaults.
3. Require review approval before sending.

## Validation
1. Replay one critical event.
2. Verify draft creation quality and completeness.
3. Verify approved path to send and rejected path to rewrite.

## Fallback
- Dead-letter path: `todo.create_manual_comms_task`
- Manual communications template if AI draft generation fails.
