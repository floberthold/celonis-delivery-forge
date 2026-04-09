# Data Quality Breach Stopline

## Outcome
Protect downstream consumers by pausing propagation on quality breaches.

## Source spec
- `../specs/data-quality-breach-stopline.json`

## Setup
1. Define null and duplicate-rate limits.
2. Set pause target and owner channel.
3. Confirm rollback policy for failed pause operations.

## Validation
1. Inject synthetic quality breach.
2. Confirm sync pause command executed.
3. Confirm remediation task opened.

## Fallback
- Dead-letter path: `incident.raise`
- Resume only after data owner sign-off.
