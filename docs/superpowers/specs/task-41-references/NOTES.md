# Task 41 — visual reference notes

## Visual verification of the thinking stream (2026-05-02)

After landing the 12-task implementation plan
(`docs/superpowers/plans/2026-05-02-thinking-stream.md`), the live stack
was booted (`pnpm dev` viewer + `uv run nova` agent on the running
Pixel_6 emulator) and the brain panel was rendered at
`http://localhost:3000`. The render matched the spec on first try:

- **Three equal columns** (Game · Cognition·stream · Brain state).
- **Live indicator** green ("● live") in the top-right header.
- **Cognition · stream column header** with `INTUITION` ModeBadge to the right.
- **ThoughtStream** middle column populated in real time:
  - Decision entries with timestamp prefix + first-person reasoning
    text (rewordFirstPerson rewriting "Nova should…" → "I should…").
  - **MOOD** chip (amber) entries fired on `dopamine_high` crossings:
    "That landed better than I expected."
  - 16 entries visible at step 8 of the live game.
- **Brain state column** with FEELING / MOOD radar (red dot, low
  arousal) / DOPAMINE bar (cyan filled) / RECALLING ("No memories
  surfaced.") / footer Score · Move · Games · Best.

The **calm-state browser screenshot** was captured into the working
session as inline image (Chrome MCP `ss_1242czt92`); the file save to
disk path was not recoverable via the MCP `save_to_disk` flag, so this
notes file stands in. The emulator state at the time of capture is
saved alongside as `emulator-during-stream-verification.png`.

**ToT-state screenshot was not captured this session** — nova hit the
50-move cap before anxiety crossed the ToT trigger threshold (board
density was high but max_tile only reached 32 in this run, vs the
256-tile threshold). The architecture for `tot_block` rendering
(branches with winner highlight, `DELIBERATING` chip) is covered by
unit + component tests:
`nova-viewer/lib/stream/__tests__/deriveStream.test.ts` and
`nova-viewer/app/components/__tests__/ThoughtStream.test.tsx`.

## Resuming visual capture

To capture additional states (ToT, trauma, game-over, etc.) for the
Claude Design mockup phase:

```bash
# Boot live stack (assumes emulator + nova-viewer running):
adb shell pm clear com.idohoresh.nova2048
adb shell am start -n com.idohoresh.nova2048/com.unity3d.player.UnityPlayerActivity
cd nova-agent && UV_PROJECT_ENVIRONMENT="$HOME/.cache/uv-envs/nova-agent" uv run nova
# Open http://localhost:3000 in a browser.
# To force ToT, let the game progress until empty_cells <= 3 + anxiety > 0.6
# (typically score 800+).
# Capture with macOS Cmd+Shift+4 or `screencapture -x file.png`.
```

## Files

- `emulator-live.png` — emulator screen captured earlier in the session
  (game-over screen, score 1040, used to verify the OCR palette
  extension).
- `emulator-during-stream-verification.png` — emulator state at the
  moment of brain-panel visual review (step 49, score 252, board has
  several 16s + a 32).
