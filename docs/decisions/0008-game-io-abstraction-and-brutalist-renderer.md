# ADR-0008: game-io-abstraction-and-brutalist-renderer

**Status:** Accepted
**Date:** 2026-05-04
**Deciders:** ihoresh07@gmail.com (solo founder), principal engineer (red-team review)

---

## Context

Phase 0.7's cliff test (per [ADR-0007](./0007-blind-control-group-for-cliff-test.md)) requires both arms — Casual Carla and the Baseline Bot — to consume **byte-identical seeded scenarios** so the only variable being measured is the cognitive architecture. The current game-I/O stack cannot deliver that:

- `nova_agent.perception.capture.Capture` reads pixel buffers from an Android emulator over ADB. Frame timing varies. Capture quality varies (animation interpolation, lossy screencap). Two runs of the same scenario from the same seed will produce different per-frame board reads.
- `nova_agent.perception.ocr.BoardOCR` runs a nearest-neighbor classifier against a 7-value palette (`0/2/4/8/16/32/128` per CLAUDE.md gotcha #6). Tile values `64` and `256` are unsampled. Higher values are total dark space. OCR error is a real confound, not a hypothetical one.
- `nova_agent.action.adb.ADB.swipe` waits 0.3s post-keyevent for the Unity tile-slide animation. Animation timing has small per-run jitter on the AVD. The game's RNG state (Unity's spawn) advances at slightly different real-time moments per run; the agent's perception of the post-spawn board may capture pre- or mid-animation depending on contention.
- The Unity 2048 fork stores save state outside app data (gotcha #7), so `pm clear` doesn't fully reset between runs. Cold-booting the AVD per scenario adds ~30s overhead per game, ×40 games per scenario × 3-5 scenarios = 1-2 hours of pure boot overhead per cliff-test run.

For the cliff test to be **falsifiable**, the spawn stream and the per-move board state must be reproducible across N=20 trials per arm × 2 arms × 3-5 scenarios = 120-200 games per cliff-test run. The live emulator pipeline cannot deliver this. A pure-Python in-process simulator can.

But adding a sim is not just "write the simulator" — it's "swap the lower I/O layer of `main.run` without contaminating the cognitive layer." Today (`nova-agent/src/nova_agent/main.py:107-122`) `Capture`, `BoardOCR`, and `ADB` are instantiated and wired inline inside the loop. A naive `if use_sim: ... else: ...` branch would create two parallel code paths in the cognitive loop, and any divergence between them (a bug, a timing assumption, a side-effect ordering) would directly contaminate the cliff test by introducing an uncontrolled variable.

There is also a second-order concern: the cognitive layer feeds `screenshot_b64` (PNG bytes → base64) to the VLM on every move (`main.py:195-196`). Without an emulator, what does the sim send? Three options: (a) render a real PNG, (b) send a synthetic placeholder, (c) refactor decider signatures to drop the image entirely. (b) and (c) change the prompt template shape across Week-0 calibration runs and Phase-0.7 cliff-test runs — that's an uncontrolled variable across the comparison and the result of "Carla-with-image vs Baseline-without-image" is uninterpretable.

The decision needs to address both: how to swap the I/O layer cleanly, and how to keep the prompt template structurally identical when the image source changes.

## Decision

**Two coupled architectural commitments:**

### 1. Introduce a `GameIO` protocol with two implementations

Define a three-method `Protocol` in `nova_agent/action/` (or a new module — implementation detail; the spec at `docs/superpowers/specs/2026-05-04-game2048sim-design.md` proposes the exact layout):

```python
class GameIO(Protocol):
    def read_board(self) -> BoardState: ...
    def apply_move(self, direction: SwipeDirection) -> None: ...
    def screenshot_b64(self) -> str: ...
```

`LiveGameIO` wraps the existing `Capture + BoardOCR + ADB` triple (refactor of today's inline code, no semantic change). `SimGameIO` wraps `Game2048Sim + brutalist renderer` (new). `main.run()` takes a `GameIO` instance and is otherwise source-agnostic. A `build_io(s: Settings)` factory picks the implementation from `Settings.io_source: Literal["live", "sim"] = "live"`.

The cognitive layer (memory, affect, decision, reflection) does not know which `GameIO` it's running against. This is the only acceptable seam — anything coarser leaks emulator-specific details upward; anything finer (e.g. separate protocols for read / move / screenshot) fragments the I/O surface across multiple injection points.

### 2. The sim's renderer is BRUTALIST and uses Pillow

`SimGameIO.screenshot_b64` returns a base64-encoded PNG produced by a single `render_board(board: BoardState) -> bytes` function with these pinned constants:

- 400×400 RGB output, 100×100 per cell, 4×4 grid
- One solid color per power of 2 (table in spec §Brutalist renderer)
- `ImageFont.load_default()` — no font-file dependency
- ~30 LoC budget; >50 LoC is a stop-and-review signal
- No animations, no UI chrome, no score panel, no game-over overlay

Pillow is already a direct dependency (`pillow>=10.3.0`, currently 12.2.0 in the env). Zero new install cost.

The renderer's only job is to produce a payload **structurally identical** to what the emulator pipeline sends — same media type (PNG), same encoding (base64 ASCII), same approximate pixel dimensions, same per-tile text legibility for the VLM. Pixel-perfect Unity-fork match (specific hex colors, drop shadows, rounded corners, animations) is **explicitly rejected** as scope creep. VLMs anchor on contrast and pattern, not on RGB precision; matching Unity's exact palette burns LoC for zero scientific value.

## Alternatives considered

- **Option A — Branch `main.run()` directly with `if use_sim:` blocks.** Easiest to write, but every divergence between the two branches is a future cliff-test contaminant. Rejected: the whole point of the sim is *removing* uncontrolled variables; introducing branched code paths in the cognitive loop adds them back.

- **Option B — Extend `Capture` to return a synthetic image when no ADB device is present.** Polymorphism by environment instead of by injected dependency. Rejected: hides the source-of-truth in environment state, makes the test path implicit, breaks the "the cognitive layer doesn't care about its source" invariant by making `Capture` itself game-aware.

- **Option C — Drop the image from the VLM payload entirely; refactor the decider signatures.** Cleanest long-term shape if the agent design moves to text-only board input. Rejected for this phase: the existing Week-0 calibration runs were performed *with* image input, and the cliff test must use the same prompt template to be a controlled comparison. Switching template shape midway between Week-0 and Phase-0.7 contaminates the result.

- **Option D — Pixel-faithful Unity-fork render (match exact hex codes, animations, shadows).** Tempting on aesthetic grounds. Rejected: VLMs aren't trained on Unity's tile palette specifically; structural identity (tile separation, value legibility, contrast-by-magnitude) is what matters for the model's spatial reasoning. Pixel-faithful matching trades engineering time for zero VLM-recognition gain. The brutalist renderer is the YAGNI-respecting choice.

- **Option E — Separate I/O protocols for read / move / screenshot (three injectables).** Finer-grained but practically worse: the three methods are always used together in the loop, and splitting them would force `main.run()` to coordinate three parameters where one suffices. Cohesion outweighs the small flexibility win.

- **Option F — Sim that bypasses the bus / publishes synthetic events directly.** Would speed up dev iteration but creates a second code path to maintain in parallel with the live one. Rejected: sim is upstream of the bus, not parallel to it. The same `bus.publish` calls in `main.run` fire whether the source is live or sim. The existing recorder/replayer (`nova_agent/bus/{recorder,replayer}.py` from PR #2) already handles the "replay an event stream" use case for UI dev — sim doesn't need to overlap with that.

## Consequences

### Positive

- **Cliff test becomes falsifiable.** Both arms (Carla, Baseline Bot) consume byte-identical seeded spawn streams from the same `Game2048Sim(seed=scenario.seed)` calls. Per-move board state is fully deterministic until the agents' decisions diverge, at which point the divergence is measured (which is the point of the test).
- **OCR + emulator + ADB latency removed as confounds.** Per-game cost drops from ~3-4s/move to milliseconds; cliff-test budget drops from hours to minutes for the non-LLM portion. LLM cost dominates and is unchanged (~$0.016 / 50 moves at flash-tier).
- **Cognitive layer remains game-agnostic** above the `GameIO` interface, codifying the implicit invariant from `.claude/rules/nova-agent.md` ("cognitive layer is game-agnostic above the perception/action interface") into actual type machinery.
- **`LiveGameIO` extraction makes the live path testable** — today's inline `Capture + OCR + ADB` wiring is hard to mock cleanly; the adapter form lets tests drive the cognitive layer without an emulator while still exercising the real `LiveGameIO` semantics.
- **Future game adapters land at a defined seam.** If/when Phase 4+ adds game-2 (likely Solitaire or a match-3, per the roadmap), it implements `GameIO` and plugs in. No cognitive-layer changes required.
- **Prompt template stays a controlled variable.** Image input survives the swap; calibration data from Week 0 stays comparable to cliff-test data from Phase 0.7.

### Negative

- **Refactor risk.** `LiveGameIO` is a behavioural-equivalent extraction of currently-inline code. Subtle ordering or caching bugs (especially around the `Capture.grab_stable` / `to_vlm_bytes` pair) could break the live path silently. Mitigation: 50-move side-by-side smoke test against the pre-refactor logs before merging the implementation PR.
- **Two render targets to keep in sync.** Brutalist renderer + Unity-fork visual style will diverge over time as the Unity build evolves. Acceptable: structural identity (what the VLM consumes) is the invariant; visual drift on the human-facing Unity build is fine.
- **Sim PNG vs emulator PNG palette mismatch is a residual risk.** Carla's behavior on sim-rendered boards may diverge from her behavior on emulator boards (different colors → potentially different VLM attention). Mitigated by a pre-Phase-0.7 calibration: 50-move sim game vs 50-move live game, same seeded sequence, compare decision distributions. If divergence exceeds a tolerance threshold (TBD with the cliff-test scenario design), tighten palette matching before running the cliff test.
- **`Game2048Sim` is a second source of truth for 2048 rules.** The Unity build has its own implementation; the sim has another. Risk of subtle disagreement on the 4 canonical merge edge cases. Mitigated by pinning the 4 cases as test fixtures (per spec §Test plan); any future Unity-fork update that changes 2048 rules requires a corresponding test update.

### Neutral

- **Sim is upstream of the existing bus + recorder/replayer.** Sim runs publish through the same `EventBus` (or `RecordingEventBus` if `NOVA_BUS_RECORD` is set) the live runs use. No new persistence layer; no new replay layer. The sim simply changes what `read_board` returns, not what happens to the resulting events.
- **`Settings.tier` and `NOVA_TIER` (per ADR-0006) compose cleanly with `Settings.io_source`.** A `dev`-tier sim run for fast iteration, a `production`-tier sim run for the cliff test (per ADR-0006: "cliff test runs at NOVA_TIER=production, forbidden from plumbing"). Independent dimensions.

### Reversibility

- **`GameIO` protocol:** moderately reversible. Reverting collapses `LiveGameIO` back into inline `main.run()` code (mechanical refactor; Git history shows the exact before-state). 1-2 hours of effort.
- **Brutalist renderer commitment:** fully reversible. If we later want pixel-faithful Unity-fork render for some reason, the renderer signature stays the same and only the function body changes. ~half a day of effort per faithfulness step.
- **`Game2048Sim` engine:** structurally reversible (delete `lab/`, revert factory) but practically irreversible — the cliff test depends on it; reversing means losing the cliff test's falsifiability story. Not a decision we'd revisit without a new ADR.

## References

- [ADR-0005](./0005-defer-v1-demo-until-phase-0.7.md) — defers v1.0.0 demo until Phase 0.7 passes; reallocates Week 0 Days 3-4 to early `Game2048Sim` build, motivating "build the sim now"
- [ADR-0006](./0006-cost-tier-discipline-and-record-replay.md) — cost-tier discipline; cliff test runs at `production` tier, sim composes with the tier system
- [ADR-0007](./0007-blind-control-group-for-cliff-test.md) — Blind Control Group cliff-test design; the load-bearing reason both arms need byte-identical seeded scenarios that only the sim can deliver
- [`docs/superpowers/specs/2026-05-04-game2048sim-design.md`](../superpowers/specs/2026-05-04-game2048sim-design.md) — full design spec for `Game2048Sim`, the brutalist renderer, the `Scenario` library, and the test plan
- `nova-agent/src/nova_agent/main.py:107-198` — current inline I/O wiring that this ADR refactors
- `.claude/rules/nova-agent.md` — "cognitive layer is game-agnostic above the perception/action interface" — the invariant this ADR codifies into the type system
- CLAUDE.md gotcha #6 (OCR palette gaps) and gotcha #7 (`pm clear` doesn't reset save state) — concrete confounds the sim removes
- Implementation commit SHAs to be added when the implementation chain merges
