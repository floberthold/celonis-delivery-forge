# Priority Case Auto Routing

## Outcome
Route priority cases consistently to correct owners.

## Source spec
- `../specs/priority-case-auto-routing.json`

## Setup
1. Configure routing matrix by domain and priority.
2. Define default queue owner.
3. Set owner notification channel.

## Validation
1. Replay P1, P2, and unmapped test cases.
2. Confirm assignment and fallback queue behavior.
3. Confirm response-time tracking starts on assignment.

## Fallback
- Dead-letter path: `todo.assign_default_queue`
- Temporary manual routing rule if matrix is unavailable.
