# Thinking Stream — viewer pane design

**Date:** 2026-05-02
**Owner:** Project Nova v1.0.0 demo
**Status:** Approved (brainstorm) → ready for implementation plan
**Successor:** to be authored via `superpowers:writing-plans`

## Goal

A live, scrollable feed in the brain-panel viewer that shows nova's
ongoing internal monologue — first-person reasoning per move, the full
process when ToT deliberation kicks in, mode flips, surfaced memories,
trauma triggers, and game-over moments — in chronological order.

This is the demo's centerpiece. It's what makes "watching nova think"
viscerally legible without requiring the viewer to read raw bus events.

## Non-goals

- Not a debug log. Raw event JSON is not displayed.
- Not a replacement for the existing `MoodGauge` / `DopamineBar` widgets;
  those already convey continuous state and do it better than text would.
- Not editable / interactive. Read-only stream.
- Not retained across sessions. In-memory only; on page reload the stream
  starts empty.

## Voice

**First-person internal monologue.** Every line reads as if overheard
from nova's mind:

> The 8 in the corner is starting to lock in. I'll consolidate down.
>
> Score 56→72. Better than expected.
>
> Anxiety just crossed 0.6 — switching to deliberation.

Source data is the LLM's third-person `decision.reasoning` field. The
viewer rewords at presentation time using a small set of templates +
pass-through where the underlying text already reads first-person. We do
**not** change the LLM prompts; this is purely a viewer-layer
transformation.

For affect-threshold crossings, the viewer formats them itself
("Anxiety just crossed 0.6 — switching to deliberation"). For ToT
branch reasoning, the LLM-supplied per-branch text is used verbatim,
indented and prefixed with the action arrow.

## Layout

Three equal columns at the top level, replacing the current `grid-cols-3`
of `[GameStream | BrainPanel]` (1/3 + 2/3) layout in `app/page.tsx`.

```
┌──────────────┬──────────────────┬──────────────┐
│  Game        │  Cognition ·     │  Brain state │
│  (scrcpy     │  Stream          │              │
│   placeholder│  (centerpiece —  │  · FEELING   │
│   stays)     │   stream lives   │  · MOOD      │
│              │   here)          │  · DOPAMINE  │
│              │                  │  · RECALLING │
│              │                  │  · stats     │
└──────────────┴──────────────────┴──────────────┘
```

The header (`Project Nova — brain panel`, live indicator) and the
`TraumaIndicator` overlay remain at the page level above the grid.

## Event filtering

The bus emits the following per-move event types:
`perception`, `decision`, `affect`, `memory_write`, `memory_retrieved`,
`mode`, `tot_branch`, `tot_selected`, `trauma_active`, `game_over`.

The stream renders a **curated** subset — every move surfaces some entry
in the stream, but routine bookkeeping events are dropped to keep the
feed legible:

| Event              | Action                                                                 |
|--------------------|------------------------------------------------------------------------|
| `perception`       | **Drop** — score/move are in the stats footer; raw board not narrative.|
| `decision`         | **Show** — one entry per move using the LLM's reasoning + chosen action. |
| `affect`           | **Drop** raw — `MoodGauge` / `DopamineBar` already render continuously. |
| affect crossings   | **Show** — synthesized entry when `anxiety > 0.6` or `valence < -0.4` or `dopamine > 0.6` (one-shot per crossing; suppress repeats until value crosses back). |
| `memory_write`     | **Drop** — boring; every move writes a record.                          |
| `memory_retrieved` | **Show** — only when the returned set is non-empty (rare in early game).|
| `mode`             | **Show** — when arbiter flips between `react` and `tot`.                |
| `tot_branch`       | **Show** — all 4 branches, indented under the parent ToT entry.         |
| `tot_selected`     | **Show** — final pick; replaces the parent's pending state.             |
| `trauma_active`    | **Show** — explicit entry with `trauma` chip.                           |
| `game_over`        | **Show** — divider entry with the post-game lesson if available.        |

## ToT presentation

When ToT triggers, the stream shows:

1. A leading first-person entry: `"I need to slow down. Let me weigh all four moves."` (text fixed in the viewer, surfaced when `mode` flips to `tot`).
2. Four indented branch entries, one per direction, each rendered as the branches return (parallel — order is whichever finishes first):
   ```
   ↳ up    — leaves my 16 exposed in the corner.   0.31
   ↳ left  — opens a merge chain on row 0.         0.42
   ↳ down  — consolidates everything to bottom.    0.58 ✓
   ↳ right — blocks the 16 from merging.            0.19
   ```
   The winning branch is rendered with the accent color (cyan) and a `✓`.
3. A trailing entry: `"Going with down."` (formatted from `tot_selected.action`).

All five entries belong to a single ToT block visually (style B — boxed
with cyan border, see Visual Hierarchy below). Branches that fail to
parse (the previous "ToT produced no valid candidates" failure mode)
render as `↳ <dir> — couldn't see this clearly.` with a faded marker
rather than disappearing silently.

## Visual hierarchy (boxed)

Each entry is rendered as a small card with a typed border + tinted
background. Tailwind/CSS:

| Type              | Border                  | Background tint      | Chip                |
|-------------------|-------------------------|----------------------|---------------------|
| routine `decision`| `rgba(255,255,255,0.04)`| `rgba(255,255,255,0.02)` | none — flush text |
| `mode` flip       | `rgba(56,189,248,0.40)` | `rgba(56,189,248,0.06)`  | `MODE` (cyan)       |
| ToT block         | `rgba(168,85,247,0.40)` | `rgba(168,85,247,0.06)`  | `DELIBERATING` (purple) |
| `memory_retrieved`| `rgba(74,222,128,0.30)` | `rgba(74,222,128,0.04)`  | `RECALLED` (green)  |
| `trauma_active`   | `rgba(248,113,113,0.45)`| `rgba(248,113,113,0.08)` | `TRAUMA` (red)      |
| affect crossing   | inherits routine        | inherits routine     | `MOOD` (amber)      |
| `game_over`       | full-width separator    | none                 | `GAME OVER` (red)   |

Type label chips: 9px, uppercase, 0.1em letter-spacing, padded `1px 6px`,
border-radius `3px`. Color-matched background and foreground per the
table.

Each entry has a subtle timestamp prefix (`14:31:02 ·`) in `text-stone-600`
for chronological anchoring; routine entries can hide it on hover-elsewhere
to reduce density.

## Motion (subtle)

- **New entry:** 320ms `opacity 0 → 1` fade-in. No translate, no slide.
- **ToT branches:** appear individually as branches return (each branch
  gets the same 320ms fade); the winning branch's `✓` and accent color
  cross-fade in once `tot_selected` arrives.
- **Trauma entry:** the entry itself plays a soft red wash via
  `box-shadow` for 800ms (`0 → 30px glow → 0`) on first render.
- **Mode flip:** no extra animation beyond the fade-in; the colored chip
  + border carry the signal.
- **Auto-scroll:** smooth scroll to bottom on each new entry while the
  stream is "stuck to live".

No bouncing, no dramatic transitions. The motion supports the live feel
without exhausting the eye over 50+ moves.

## Pacing + retention + scroll

- **Auto-scroll behavior:** sticky-bottom by default. As entries arrive,
  the stream auto-scrolls so the latest is visible.
- **Detach on user scroll-up:** if the user scrolls up by more than ~24px
  from the bottom, sticky-mode releases. A small floating chip appears
  bottom-right: `↓ jump to live (3 new)`. Clicking it re-engages
  sticky-mode and snaps to the bottom.
- **Bounded history:** keep the last **100 entries** in the DOM. Older
  entries are removed (no fade-out animation; they simply disappear once
  the buffer is full and a new entry pushes the oldest out).
- **Coalescing:** none in v1. Each move emits one `decision` entry even
  if the prior move was identical. We can revisit if the stream becomes
  noisy in observed sessions.
- **Game boundaries:** a `game_over` entry renders as a full-width
  divider with the post-game lesson; the next game's first `decision`
  appears on the line below. No clear/reset between games — the stream
  is one continuous transcript bounded only by the 100-entry cap.

## Component contract

A single new component `ThoughtStream` lives at
`nova-viewer/app/components/ThoughtStream.tsx`.

### Inputs

```ts
interface Props {
  events: AgentEvent[];          // already in app/page.tsx state via useNovaSocket
  affect: AffectVectorDTO;       // current affect, used for crossing detection
}
```

### Internal state

- Derived list of `StreamEntry` (typed union — see below).
- Sticky-bottom flag controlled by user scroll position.
- "New since detach" counter for the jump-to-live chip.

### Outputs

Pure presentational; no callbacks, no global state mutation.

### `StreamEntry` shape

```ts
type StreamEntry =
  | { kind: "decision"; ts: string; text: string; action: Action; confidence: number }
  | { kind: "affect_crossing"; ts: string; text: string }
  | { kind: "mode_flip"; ts: string; from: Mode; to: Mode; text: string }
  | { kind: "tot_block"; ts: string; lead: string; branches: ToTBranchEntry[]; selected?: { action: Action; trailer: string } }
  | { kind: "memory_recalled"; ts: string; text: string; count: number }
  | { kind: "trauma"; ts: string; text: string }
  | { kind: "game_over"; ts: string; lesson?: string };

type ToTBranchEntry = {
  action: Action;
  value: number | null;     // null when parse failed
  reasoning: string;        // "couldn't see this clearly" if parse failed
  status: "pending" | "complete" | "parse_error";
};
```

### Event derivation

Pure function `deriveStream(events: AgentEvent[], prevAffect: AffectVectorDTO | null): StreamEntry[]`.

- Walks events in order; emits one `StreamEntry` per material event per
  the filtering rules above.
- Maintains a small reducer state internally for: pending ToT block (so
  `tot_branch` events accumulate under the current block, and
  `tot_selected` patches the same entry instead of creating a new one);
  current mode (so `mode` events generate transitions); previous affect
  values (for crossing detection).
- Returns the derived list, capped to the latest 100 entries.

The function is unit-testable in isolation against fixture event arrays.

## Page integration

`app/page.tsx`:

1. Change the top-level grid from `grid-cols-3` (1+2) to three equal
   columns: `grid-cols-3 grid-cols-[1fr_1fr_1fr]` (or simply
   `grid-cols-3` with the new BrainPanel filling its column).
2. Decompose the existing `<BrainPanel ... />` block into two siblings:
   `<ThoughtStream events={events} affect={affect} />` (middle column)
   and a slimmed `<BrainPanel ... />` (right column) containing only
   `AffectLabel`, `MoodGauge`, `DopamineBar`, `MemoryFeed`,
   `StatsFooter` + the existing header.
3. Drop the stale "Cognition" header on the slimmed BrainPanel — the
   middle column gets that label now.

## Out of scope (for this v1 of the stream)

- Audio cues on mode flip / trauma.
- Per-game replay / scroll back to a specific move.
- Export of the stream transcript to a file at end-of-game.
- Sentiment-aware coloring of routine `decision` entries based on
  current affect (would be a nice polish later).
- Real-time word-by-word streaming of LLM tokens. Each entry appears
  fully formed when its source event lands.

## Risks + open questions

- **Verbosity of `decision.reasoning`.** Some Gemini Flash outputs are
  3–4 sentences. The stream entry should render full text but truncate
  at ~240 chars with an inline `…` and tooltip-on-hover for the full
  reasoning. (Open: confirm 240 vs 180 from observed data.)
- **First-person rewording fidelity.** Gemini's reasoning is sometimes
  third-person ("Nova should swipe…"). The viewer's reword logic must
  detect this and pronoun-swap. Not all cases will be clean; design for
  graceful pass-through when the rewrite is uncertain.
- **Trauma re-firing.** `trauma_active` can fire multiple consecutive
  moves. The stream coalesces consecutive trauma events into a single
  entry and increments a counter ("× 3") rather than spamming.
- **ToT branches that all fail.** Currently this raises in the agent.
  The viewer should still render the failed `tot_block` with all
  branches as `parse_error` and a trailing "had to fall back" entry, so
  even a degraded ToT moment is visible.

## What this enables for Task 41

Task 41 (Claude Design static states) needs concrete mockups for: Calm,
Anxious + trauma, Frustrated, Dopamine spike, Trauma glow, ToT mode,
Game-over. With the stream design locked, each of those becomes a known
combination of `StreamEntry.kind`s + chip colors + container state. The
Task 41 mockups can be generated from real session screenshots once
this is built.
