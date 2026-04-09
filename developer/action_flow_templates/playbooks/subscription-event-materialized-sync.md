# Subscription Event Materialized Sync

## Outcome
Maintain near-real-time projections from subscription events.

## Source spec
- `../specs/subscription-event-materialized-sync.json`

## Setup
1. Register subscription and projection schema.
2. Define required projection fields.
3. Set DLQ destination for failed events.

## Validation
1. Replay create and update events.
2. Verify projection upserts and keys.
3. Confirm DLQ threshold alerting behavior.

## Fallback
- Dead-letter path: `dlq.write`
- Trigger reprocessing job for DLQ batches.
