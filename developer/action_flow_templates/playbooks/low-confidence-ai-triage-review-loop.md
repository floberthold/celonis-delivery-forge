# Low Confidence AI Triage Review Loop

## Outcome
Prevent low-confidence AI outputs from bypassing human review.

## Source spec
- `../specs/low-confidence-ai-triage-review-loop.json`

## Setup
1. Set confidence threshold.
2. Define reviewer pool and SLA.
3. Configure feedback persistence target.

## Validation
1. Replay low-confidence payload.
2. Confirm review task creation and assignment.
3. Confirm corrected label stored in feedback table.

## Fallback
- Dead-letter path: `notify.ai_review_backlog`
- Pause AI-driven auto-apply until backlog clears.
