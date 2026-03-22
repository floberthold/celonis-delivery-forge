# Agent Sprite Pack

This folder now includes built-in original sprites created for the orchestration town map.

Included sprite keys:
- `builder`
- `guardian`
- `scout`
- `courier`

Provided files:
- `builder.svg`
- `guardian.svg`
- `scout.svg`
- `courier.svg`

Runtime behavior:
- Map renderer loads from `/static/sprites/agents/<sprite_key>` and tries `.png` first, then `.svg`.
- If both formats are missing, the renderer falls back to a colored marker so the UI remains usable.

Asset guidance:
- Keep transparent backgrounds.
- Use square frames (32x32, 48x48, or 64x64).
- Keep the character centered in frame.
