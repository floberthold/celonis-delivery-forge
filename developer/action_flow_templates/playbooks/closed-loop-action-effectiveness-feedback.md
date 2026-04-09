# Closed Loop Action Effectiveness Feedback

## Outcome
Measure and feed action effectiveness into prioritization.

## Source spec
- `../specs/closed-loop-action-effectiveness-feedback.json`

## Setup
1. Define baseline and observed metrics.
2. Configure weekly cadence and owner.
3. Bind output fields to recommendation prioritization inputs.

## Validation
1. Run one weekly cycle with known historical actions.
2. Confirm effectiveness score generation.
3. Confirm priority model update event.

## Fallback
- Dead-letter path: `todo.create_manual_feedback_task`
- Manual KPI update if automated write fails.
