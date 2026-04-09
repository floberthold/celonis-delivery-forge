# Action-Flow Best Practices

Use this guide to design and roll out reliable action flows inspired by Make-style scenario patterns.

## Design Rules

1. One trigger contract per flow.
2. One business outcome per flow.
3. Explicit idempotency key for side-effecting actions.
4. Explicit dead-letter behavior and owner.

## Error-Handling Policy

- `break`: use for unsafe state and critical validation failures.
- `retry`: use for temporary external failures with bounded retries.
- `resume`: use with substitute values when flow continuity is acceptable.
- `ignore`: use only for non-critical notifications.
- `rollback`: use when partial writes must be reverted.
- `commit`: use when preserving partial progress is safer than rollback.

## Reliability Defaults

- Enable sequential processing for high-risk templates.
- Store incomplete executions for medium/high risk templates.
- Set max retries <= 3 unless reviewer approves exception.
- Test one happy path and one failure path before promotion.

## Governance Checklist

- Owner and reviewer roles defined.
- Review cadence defined.
- Evidence bundle captured (logs, timeline links, decision).
- Rollback or fallback tested in sandbox.
