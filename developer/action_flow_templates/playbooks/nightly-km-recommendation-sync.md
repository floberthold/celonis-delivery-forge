# Nightly Knowledge Model Recommendation Sync

## Outcome
Keep downstream systems aligned with latest KM recommendations.

## Source spec
- `../specs/nightly-km-recommendation-sync.json`

## Setup
1. Configure KM endpoint and target system connection.
2. Set batch size and lookback window.
3. Validate idempotency key behavior.

## Validation
1. Run one nightly cycle in sandbox.
2. Verify upsert counts against source counts.
3. Confirm summary event in timeline.

## Fallback
- Dead-letter path: `sync_queue.enqueue`
- Run manual catch-up sync if queue backlog grows.
