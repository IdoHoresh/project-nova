# Game2048Sim — pure-Python in-process 2048 simulator

**Date:** 2026-05-04
**Owner:** Project Nova — Phase 0.7 cliff-test infrastructure
**Status:** Approved (brainstorm) → ready for implementation plan
**Successor:** to be authored via `superpowers:writing-plans`
**Related ADRs:** [ADR-0005](../../decisions/0005-defer-v1-demo-until-phase-0.7.md), [ADR-0006](../../decisions/0006-cost-tier-discipline-and-record-replay.md), [ADR-0007](../../decisions/0007-blind-control-group-for-cliff-test.md)
**Companion ADR:** [ADR-0008](../../decisions/0008-game-io-abstraction-and-brutalist-renderer.md) — `GameIO` abstraction + brutalist renderer rationale (Accepted, 2026-05-04)

---

## Goal

Build a pure-Python in-process 2048 simulator that exposes the same
`BoardState` interface the cognitive layer already consumes, plus a
brutalist renderer that produces a structurally-identical PNG payload
to what the live emulator pipeline sends.

Removes three confounds from the Phase 0.7 cliff test:
- OCR error (per `nova_agent/perception/ocr.py` palette gaps)
- Emulator boot + ADB IPC latency (~3-4s/move → milliseconds)
- Unity-fork-specific behaviour drift (e.g. animation timing, save-state
  side effects)

The cognitive layer (memory, affect, decision, reflection) is unchanged.
The change introduces a `GameIO` protocol that abstracts the existing
`Capture + BoardOCR + ADB` triple, with two implementations:
`LiveGameIO` (refactor of today) and `SimGameIO` (new).

## Non-goals

- **Not a Baseline Bot.** The Bot is a separate cognitive subsystem with
  its own decision logic; this spec only ensures the Bot will be able to
  consume `Game2048Sim` deterministically when its own spec lands.
- **Not a graphical simulator.** No animations, no UI chrome, no game
  panels. The renderer is functional, not visual.
- **Not a Unity-fork-faithful clone.** Behavioural conformance to the 4
  canonical 2048 merge edge cases (below) is the bar; pixel-faithful
  reproduction of the Unity build's tile colours / fonts / shadows is
  explicitly rejected as scope creep.
- **Not a replay tool.** The existing bus recorder/replayer
  (`nova_agent/bus/recorder.py`, `replayer.py`) handles event-stream
  replay. The sim is upstream of the bus, not a bus consumer.
- **Not a multi-game framework.** This spec is 2048-only. The `GameIO`
  protocol is the seam where new games would later plug in (Phase 4+).

## Why now (vs Week 1)

Per [ADR-0005](../../decisions/0005-defer-v1-demo-until-phase-0.7.md),
the v1.0.0 demo recording is deferred until Phase 0.7 cliff test passes.
Days 3-7 of Week 0 (originally demo prep) are reallocated to early
`Game2048Sim` build, so the cliff test can begin on Day 1 of Week 1
instead of Day 3.

Per [ADR-0007](../../decisions/0007-blind-control-group-for-cliff-test.md),
the cliff test is two-armed (Carla + Baseline Bot, same seeded sequences,
N=20 each per scenario). The pass criterion `Δ ≥ 2` (lead time) requires
both arms to consume identical scenario seeds — only the sim can deliver
this. The live emulator pipeline cannot (ADB timing varies, OCR
non-determinism).

---

## Architecture

### The `GameIO` protocol (the load-bearing seam)

```python
from typing import Protocol
from nova_agent.action.adb import SwipeDirection
from nova_agent.perception.types import BoardState


class GameIO(Protocol):
    """Game-agnostic I/O surface used by the cognitive layer.

    Two implementations exist:
    - LiveGameIO: wraps Capture + BoardOCR + ADB (live emulator)
    - SimGameIO: wraps Game2048Sim + brutalist renderer (in-process)

    The cognitive layer (decision/affect/memory/reflection) MUST NOT
    instantiate either implementation directly. main.run() takes a
    GameIO instance and is otherwise source-agnostic.
    """

    def read_board(self) -> BoardState:
        """Return the current board state (4x4 grid + score)."""
        ...

    def apply_move(self, direction: SwipeDirection) -> None:
        """Apply a move. Sim: deterministic merge + spawn.
        Live: ADB keyevent + animation wait."""
        ...

    def screenshot_b64(self) -> str:
        """Return a base64-encoded PNG of the current board state.
        Sim: brutalist renderer output. Live: emulator screen capture."""
        ...
```

### Refactor: `main.run()` becomes source-agnostic

Today (`main.py:107-122`):
```python
capture = Capture(adb_path=s.adb_path, device_id=s.adb_device_id)
adb = ADB(adb_path=s.adb_path, device_id=s.adb_device_id, screen_w=1080, screen_h=2400)
ocr = BoardOCR()
# ... loop uses capture.grab_stable() + ocr.read() + adb.swipe() inline
```

After:
```python
io: GameIO = build_io(s)  # picks LiveGameIO or SimGameIO from settings
# ... loop uses io.read_board(), io.apply_move(), io.screenshot_b64()
```

`build_io(s)` reads a new `Settings.io_source: Literal["live", "sim"] = "live"`
field and instantiates the appropriate `GameIO`. Default stays `"live"` so
existing behaviour is unchanged when no env var is set.

### Module layout

```
nova-agent/src/nova_agent/
├── lab/                          # NEW
│   ├── __init__.py
│   ├── sim.py                    # Game2048Sim engine (rules + RNG)
│   ├── render.py                 # Brutalist PNG renderer
│   ├── scenarios.py              # Scenario dataclass + library
│   └── io.py                     # SimGameIO implementation
├── action/
│   ├── adb.py                    # unchanged
│   └── live_io.py                # NEW — LiveGameIO wrapper (refactor)
└── main.py                       # MODIFIED — uses GameIO via build_io()
```

`live_io.py` is a tiny adapter that holds existing `Capture` + `BoardOCR` +
`ADB` instances and exposes them through the `GameIO` protocol. Today's
inline call sites in `main.py` move into this adapter, no semantic change.

`io.py` (in `lab/`) holds `SimGameIO` which wraps `Game2048Sim` +
`render.py`. Same shape, different internals.

---

## Component specs

### 1. `Game2048Sim` engine (`lab/sim.py`)

**API:**

```python
@dataclass(frozen=True)
class Scenario:
    """Frozen, JSON-serializable starting condition for a game."""
    id: str                              # e.g. "cliff-001-corner-trap"
    initial_grid: list[list[int]]        # 4x4, may be all zeros for fresh start
    initial_score: int
    seed: int                            # RNG seed for spawn stream


class Game2048Sim:
    def __init__(
        self,
        seed: int,
        scenario: Scenario | None = None,
    ) -> None: ...

    @property
    def board(self) -> BoardState: ...

    def apply_move(self, direction: SwipeDirection) -> bool:
        """Apply a move. Returns True if the board changed (move was
        legal), False if the move was a no-op (same board, no spawn).

        Matches real 2048 semantics: no-op moves do NOT spawn a new tile.
        """
        ...

    def is_game_over(self) -> bool:
        """Authoritative game-over: no merges possible AND no empty cells."""
        ...
```

**Note on game-over signalling:** sim's `is_game_over()` is informational
/ test-only. The cognitive-layer loop in `main.py` continues to call the
existing `decision/heuristic.py:is_game_over(board)` heuristic, treating
the sim as a perfect oracle the heuristic should agree with. Any
divergence between `Game2048Sim.is_game_over()` and
`decision.heuristic.is_game_over()` surfaces a heuristic bug. This is
intentional — keeps the cognitive code path identical to live runs.

**Move + merge semantics — the four canonical edge cases (pin in tests):**

1. **Single-merge per tile per move.**
   `[2, 2, 4, 0]` swipe-left → `[4, 4, 0, 0]` (the resulting `4` does NOT
   re-merge with the existing `4` in the same step).
2. **Leftmost / first-encountered priority.**
   `[2, 2, 2, 2]` swipe-left → `[4, 4, 0, 0]`, NOT `[2, 4, 2, 0]` or
   `[4, 0, 4, 0]`. Pairs form from the swipe direction.
3. **No-op swipe = no spawn.**
   `[2, 0, 0, 0]` swipe-left → unchanged. `apply_move` returns `False`,
   no new tile spawned, RNG state unaffected.
4. **Spawn ratio 90% `2` / 10% `4`.**
   After a successful move, exactly one new tile spawns at a uniformly
   random empty cell, value 2 with probability 0.9 or 4 with probability
   0.1. Both draws use the same seeded RNG instance.

**Scoring:**
- Score increments by the value of every tile produced by a merge in
  this move (e.g. merging two 8s → +16).
- Per-move score delta is the sum across all merges in that move.

**RNG:**
- `Game2048Sim` owns a single `random.Random(seed)` instance.
- All randomness (spawn position, spawn value 2-vs-4) draws from this
  instance, in a fixed order: position first, then value.
- `random.Random` is the stdlib Mersenne Twister — deterministic and
  byte-identical across Python 3.11+ for the same seed + draw sequence.

### 2. Brutalist renderer (`lab/render.py`)

**API:**

```python
def render_board(board: BoardState) -> bytes:
    """Render a 4x4 BoardState to a 400x400 PNG, return raw bytes.

    Brutalist: solid power-of-2-keyed colours, PIL default font,
    centered tile values, no chrome, no animations, no score panel.
    """
```

**Pinned constants:**
- Output: `400 × 400` RGB PNG
- Cell size: `100 × 100` pixels (4×4 grid, no inner padding for now)
- Background: `#bbada0` (Unity-fork match for visual familiarity, but
  this is the ONLY palette match — all tile colours diverge)
- Tile palette (one entry per power of 2; `0` = empty/grey):
  ```python
  PALETTE = {
      0:    "#cdc1b4",  # empty
      2:    "#eee4da",
      4:    "#ede0c8",
      8:    "#f2b179",
      16:   "#f59563",
      32:   "#f67c5f",
      64:   "#f65e3b",
      128:  "#edcf72",
      256:  "#edcc61",
      512:  "#edc850",
      1024: "#edc53f",
      2048: "#edc22e",
      4096: "#3c3a32",  # final cap; higher values get the same colour
  }
  ```
- Font: `ImageFont.load_default()` — no font-file dependency, works
  cross-platform out of the box
- Text colour: `#776e65` for tiles ≤ 4, `#f9f6f2` for ≥ 8 (matches
  Unity-fork contrast convention; cheap to match, makes VLM OCR robust)
- Total LoC budget: **~30 LoC** for `render_board`. If the implementation
  pushes past 50 LoC, that's a signal it's drifting toward over-engineering
  — stop and review.

**Why these specifics matter:** Pillow is already a dep
(`pillow>=10.3.0`, installed 12.2.0). The renderer's only job is to
produce a payload that's *structurally identical* to the emulator
pipeline's PNG-bytes-base64'd handoff to the VLM, so prompt template
shape stays a controlled variable across Week-0 calibration runs and
Phase-0.7 cliff-test runs. Pixel-perfect Unity-fork match is NOT the
goal; structural identity is.

### 3. Scenario library (`lab/scenarios.py`)

```python
from nova_agent.lab.sim import Scenario

# Phase 0.7 cliff-test scenarios. Each is a board state where a baseline
# (greedy / random) bot will fail predictably and Carla's affect signature
# should fire ahead of the failure. 3-5 scenarios per ADR-0007.
SCENARIOS: dict[str, Scenario] = {
    "fresh-start": Scenario(
        id="fresh-start",
        initial_grid=[[0] * 4 for _ in range(4)],
        initial_score=0,
        seed=2026_05_04,
    ),
    # cliff-001 through cliff-005 to be added when the scenario design
    # session lands (separate spec — Phase 0.7 prep). For now the API
    # supports loading them by id; the library starts with `fresh-start`
    # so the sim is end-to-end testable from day one.
}


def load(scenario_id: str) -> Scenario:
    """Return a frozen Scenario by id. Raises KeyError on unknown id."""
    ...
```

The "3-5 documented hard scenarios" (per CLAUDE.md Week 0 Day 5) are a
**separate design session** (Phase 0.7 prep). This spec ships the
*infrastructure* for scenarios (the `Scenario` dataclass + the library
loader) plus exactly one entry (`fresh-start`) so the sim is
end-to-end testable. Hard scenarios get authored against this loaded
infrastructure in a follow-up spec.

### 4. `SimGameIO` (`lab/io.py`)

```python
import base64
from nova_agent.lab.render import render_board
from nova_agent.lab.sim import Game2048Sim, Scenario


class SimGameIO:
    def __init__(self, sim: Game2048Sim) -> None:
        self._sim = sim

    def read_board(self) -> BoardState:
        return self._sim.board

    def apply_move(self, direction: SwipeDirection) -> None:
        self._sim.apply_move(direction)  # discard bool — match GameIO contract

    def screenshot_b64(self) -> str:
        return base64.b64encode(render_board(self._sim.board)).decode("ascii")
```

Tiny by design. Holds zero state of its own; pure adapter.

### 5. `LiveGameIO` (`action/live_io.py` — refactor of existing inline code)

```python
import base64
from nova_agent.action.adb import ADB, SwipeDirection
from nova_agent.perception.capture import Capture
from nova_agent.perception.ocr import BoardOCR, CalibrationError
from nova_agent.perception.types import BoardState


class LiveGameIO:
    def __init__(self, capture: Capture, ocr: BoardOCR, adb: ADB) -> None:
        self._capture = capture
        self._ocr = ocr
        self._adb = adb
        self._last_image = None  # cached for screenshot_b64() reuse

    def read_board(self) -> BoardState:
        self._last_image = self._capture.grab_stable()
        try:
            return self._ocr.read(self._last_image)
        except CalibrationError:
            return BoardState(grid=[[0] * 4 for _ in range(4)], score=0)

    def apply_move(self, direction: SwipeDirection) -> None:
        self._adb.swipe(direction)
        self._last_image = None  # invalidate: next read_board needs fresh capture

    def screenshot_b64(self) -> str:
        if self._last_image is None:
            self._last_image = self._capture.grab_stable()
        return base64.b64encode(Capture.to_vlm_bytes(self._last_image)).decode("ascii")
```

Behavioural-equivalent refactor of today's inline code in `main.py`.
Caches the last screenshot between `read_board` and `screenshot_b64` to
avoid a redundant ADB capture per loop step (today's loop already does
this implicitly via local variables; the cache makes it explicit).
`apply_move` invalidates the cache so the next `read_board` triggers a
fresh capture — without this, the loop would feed the post-move VLM
prompt a pre-move screenshot. This is the exact bug the explicit cache
prevents.

### 6. `build_io()` factory (`main.py`)

```python
def build_io(s: Settings) -> GameIO:
    if s.io_source == "sim":
        scenario = scenarios.load(s.sim_scenario)
        sim = Game2048Sim(seed=scenario.seed, scenario=scenario)
        return SimGameIO(sim)
    capture = Capture(adb_path=s.adb_path, device_id=s.adb_device_id)
    ocr = BoardOCR()
    adb = ADB(adb_path=s.adb_path, device_id=s.adb_device_id, screen_w=1080, screen_h=2400)
    return LiveGameIO(capture, ocr, adb)
```

New `Settings` fields (in `config.py`):
- `io_source: Literal["live", "sim"] = "live"` (env: `NOVA_IO_SOURCE`)
- `sim_scenario: str = "fresh-start"` (env: `NOVA_SIM_SCENARIO`)

Both inherit `env_ignore_empty=True` from the existing `model_config`,
so empty shell exports won't shadow defaults (gotcha #3).

---

## Determinism contract

Two arms (Carla, Baseline Bot) instantiate `Game2048Sim(seed=scenario.seed)`
independently and get **byte-identical tile-spawn streams** as long as
both arms take the same number of legal moves before each spawn AND the
same number of no-op moves (which don't consume RNG draws).

**Critical caveat — same seed ≠ identical games:**

Spawns happen *after* moves at a uniformly random empty cell. Once two
agents diverge in their decisions, the empty-cell sets diverge → spawn
positions diverge → games diverge. This is the EXPECTED behaviour for
the cliff test (we're explicitly comparing how different agents handle
the same scenario), not a bug.

What "same seed" guarantees:
- Spawn sequence (which-cell-then-2-vs-4) is byte-identical for the
  first move both arms take from the same scenario.
- For move N, spawn determinism holds if and only if both arms have
  produced identical board states up to that point.
- Equivalently: if both arms make identical decisions for the first K
  moves, their boards are identical for all K+1 ≤ N ≤ K+1 (next spawn
  matches; subsequent moves diverge as soon as decisions diverge).

What "same seed" does NOT guarantee:
- Different agents will see the same boards over the course of a game.
- Equal-length games. Different agents will hit game-over at different
  step counts.

Document this in the `Game2048Sim` docstring + reference from ADR-0008.

---

## Test plan (TDD discipline — tests written FIRST)

Tests live in `nova-agent/tests/`, alongside the existing 140+ pytest
suite. Per `.claude/rules/nova-agent.md`: TDD is mandatory for any
cognitive-layer-adjacent code. `Game2048Sim` is below the cognitive
line but the discipline still applies.

### `test_game2048sim.py` — engine (~15 tests)

- `test_fresh_start_has_two_initial_tiles`
- `test_seed_determinism_same_seed_same_first_spawn`
- `test_seed_determinism_different_seeds_different_first_spawn`
- `test_merge_single_per_tile` (edge case 1)
- `test_merge_leftmost_priority_swipe_left` (edge case 2)
- `test_merge_leftmost_priority_swipe_right`
- `test_merge_leftmost_priority_swipe_up`
- `test_merge_leftmost_priority_swipe_down`
- `test_no_op_swipe_returns_false_no_spawn` (edge case 3)
- `test_no_op_swipe_does_not_advance_rng` — concrete assertion: take two
  identical sims, in sim A do `(no-op move, then legal move)`, in sim B do
  `(legal move alone)`. After both sequences, `sim_a.board == sim_b.board`
  (same spawn position + value, because the no-op consumed no RNG draws)
- `test_spawn_ratio_2_vs_4_distribution_over_10000_spawns` (statistical:
  90% ± 1.5% for `2`, 10% ± 1.5% for `4`)
- `test_score_increments_by_merged_tile_value`
- `test_game_over_when_no_merges_and_no_empty_cells`
- `test_game_over_false_when_empty_cells_exist`
- `test_scenario_loading_from_library`

### `test_render.py` — renderer (~6 tests)

- `test_render_returns_400x400_png_bytes` (parse PNG header + dims)
- `test_render_empty_board_uses_empty_palette`
- `test_render_max_tile_2048_uses_2048_palette`
- `test_render_above_2048_uses_4096_palette`
- `test_render_total_loc_under_50` (meta-test: `render_board` source LoC
  bound — guards against drift)
- `test_render_does_not_raise_on_zero_filled_grid`

### `test_sim_game_io.py` — adapter (~3 tests)

- `test_read_board_returns_sim_board`
- `test_apply_move_advances_sim_state`
- `test_screenshot_b64_returns_valid_base64_png`

### `test_live_game_io.py` — adapter refactor (~4 tests)

- `test_read_board_invokes_capture_then_ocr` (mock both)
- `test_read_board_returns_empty_on_calibration_error`
- `test_apply_move_invokes_adb_swipe`
- `test_apply_move_invalidates_cached_image` — pin the cache-invalidation
  contract so a post-move `screenshot_b64` triggers a fresh `Capture.grab_stable`
- `test_screenshot_b64_reuses_cached_image_when_available`

### `test_main_build_io.py` — factory (~2 tests)

- `test_build_io_returns_live_game_io_by_default`
- `test_build_io_returns_sim_game_io_when_io_source_sim`

**Total new tests: ~31.** Existing 140+ test suite must remain green;
the `LiveGameIO` refactor is behavioural-equivalent and shouldn't break
anything in `main.py`'s loop.

### Integration smoke (run manually after impl)

- `NOVA_IO_SOURCE=sim NOVA_SIM_SCENARIO=fresh-start uv run nova` should
  play a full game in-process with zero ADB / emulator dependencies and
  publish all the same bus events the live loop publishes.
- Compare cost: live 50-move ≈ $0.016; sim 50-move should be in the
  same ballpark (LLM cost dominates; sim removes capture / OCR / ADB
  overhead, not LLM cost).

---

## Acceptance criteria

1. All ~30 new tests pass; existing 140+ tests still pass.
2. `uv run mypy` clean (strict mode) — no new `# type: ignore`.
3. `uv run ruff check` clean.
4. Manual smoke: `NOVA_IO_SOURCE=sim uv run nova` plays a full game
   without ADB or emulator running, publishes the same bus events as
   live, brain panel renders identically.
5. ADR-0008 written + committed (Accepted 2026-05-04, ref `b743eef`) — implementation chain references it for context on every load-bearing decision.
6. `LESSONS.md` entry added if any non-obvious surprise surfaces during
   implementation (e.g. RNG cross-version determinism caveat, Pillow
   version-specific font behaviour).

---

## Out of scope (explicit deferrals)

- **Baseline Bot implementation.** Separate spec. The Bot will consume
  `Game2048Sim(seed=scenario.seed)` exactly the way Carla will via
  `SimGameIO`; this spec only ensures the contract supports that.
- **The 3-5 hard cliff-test scenarios.** Separate spec (Phase 0.7 prep).
  Library starts with `fresh-start` only.
- **Multi-game support.** The `GameIO` protocol is the seam, but there
  are no other game adapters in this spec.
- **Recording sim runs.** The bus recorder already records from any
  source; sim runs will record automatically when `NOVA_BUS_RECORD`
  is set.
- **Performance optimisation.** ~$0.016 / 50 moves at LLM cost is
  acceptable; sim's compute cost is negligible. No micro-benchmarks
  needed at this stage.

---

## Risk register

| Risk | Severity | Mitigation |
|------|----------|------------|
| Pillow's `ImageFont.load_default()` font changes across versions, breaking visual reproducibility for the VLM | Low | Font is for VLM consumption, not human; structural identity (4×4 grid, tile values legible) is what matters. Add a `LESSONS.md` note if a VLM regression is observed. |
| Cognitive layer behaves differently with sim PNG vs emulator PNG (palette mismatch beyond the documented exceptions) | Medium | Brutalist palette diverges from Unity-fork by design. Pre-Phase-0.7 calibration run: 50-move sim game vs 50-move live game, same seed, compare decision distributions. If divergent, tighten palette matching. |
| `random.Random` Mersenne Twister determinism shifts across Python minor versions | Very Low | Stdlib MT is stable since Python 3.0; Python 3.11+ explicitly guarantees backwards compatibility for `random.Random(seed)` draw sequences. Pin Python version in CI (already done). |
| `LiveGameIO` refactor breaks the existing main loop in subtle ways | Medium | Behavioural-equivalent refactor with a 50-move smoke test BEFORE landing. Side-by-side log diff against pre-refactor 50-move log. |
| Per-event `asyncio.to_thread` cost in `RecordingEventBus` (flagged in PR #2 review) compounds with sim's higher event cadence | Low | Sim's per-move cost is dominated by LLM latency, not bus cost. If post-impl profiling shows the bus is the bottleneck, address in a follow-up PR per the existing flagged finding. |

---

## Implementation note

This spec is the WHAT. The HOW (concrete commit sequence, sub-task
decomposition, TDD red-green-refactor cadence) belongs in the
`writing-plans`-generated implementation plan that follows. Do NOT
inline a step-by-step here.

The plan will sequence:
1. `GameIO` protocol + `LiveGameIO` refactor + tests (no behaviour
   change, lands first to verify the seam works)
2. `Game2048Sim` engine + tests (TDD: tests for the 4 edge cases first,
   then implement)
3. Brutalist renderer + tests
4. `SimGameIO` adapter + tests
5. `Scenario` library + factory + Settings wiring
6. ADR-0008 + LESSONS.md if any non-obvious surprises
7. Manual smoke + sim-vs-live calibration run
