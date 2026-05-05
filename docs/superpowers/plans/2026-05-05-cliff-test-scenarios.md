# Phase 0.7 Cliff-Test Scenarios Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extend the `Scenario` dataclass with the contract pinned in the cliff-test scenarios spec (six new fields + validators + paired-seed method) and add the three cliff-test scenarios (`snake-collapse-128`, `512-wall`, `corner-abandonment-256`) plus the cross-scenario corpus invariants (`MAX_MOVES`, illusion-of-hope lower bound, palette validity).

**Architecture:** Modify `nova_agent.lab.sim.Scenario` in place — rename the existing `seed` field to `seed_base`, add a `seed(trial_index: int)` method, add five new fields with a `__post_init__` validator that enforces the minimum-implied-score formula and the grid invariants. Migrate all callers and existing test fixtures. Add three scenarios as `Scenario(...)` literals in `nova_agent.lab.scenarios.SCENARIOS`. Add a module-level `MAX_MOVES = 50` constant. New test file `tests/test_lab_scenarios.py` for corpus-level invariants; per-scenario sim-integration tests slot into the existing `tests/test_lab_sim.py`.

**Tech Stack:** Python 3.11+ (dev runs 3.14), `uv`, `pytest`, `mypy --strict`, `ruff`, `dataclasses` (frozen), no new dependencies.

**Source spec:** [`docs/superpowers/specs/2026-05-05-cliff-test-scenarios-design.md`](../specs/2026-05-05-cliff-test-scenarios-design.md) (commit `b55a36c`).

**Companion ADRs:**
- [`docs/decisions/0007-blind-control-group-for-cliff-test.md`](../../decisions/0007-blind-control-group-for-cliff-test.md) — the two-arm cliff-test design these scenarios serve
- [`docs/decisions/0008-game-io-abstraction-and-brutalist-renderer.md`](../../decisions/0008-game-io-abstraction-and-brutalist-renderer.md) — the GameIO seam scenarios run under

**Branch state on pickup:** worktree at `/Users/idohoresh/Desktop/a/.claude/worktrees/practical-swanson-4b6468`, branch `claude/practical-swanson-4b6468`, last commit `b55a36c` (the spec). 0 commits ahead of origin.

**Out of scope (do NOT bundle into this plan):**

- The Test Runner implementation — separate Phase 0.7 prep spec.
- The Baseline Bot architectural choice (LLM vs heuristic) — separate Phase 0.7 prep spec; both architectures consume `Scenario` and produce moves, so the scenarios spec is agnostic.
- Pinning specific URLs for `source_citation` — the spec deliberately leaves the citation strings as source-class descriptors and notes URL-pinning as a deferred follow-up requiring real-world verification by the user. This plan ships descriptors as-spec'd; URL pinning lands in a follow-up commit.
- Pilot calibration runs — these need the Baseline Bot spec to exist first; covered in spec §7.4 as a manual gate before the real N=20 run, not a unit test.
- Scenarios 4-5 — methodology says "3-5"; this plan ships 3 per spec §8 out-of-scope.

---

## File Structure

| Path | Action | Responsibility |
|------|--------|----------------|
| `nova-agent/src/nova_agent/lab/sim.py` | Modify | Extend `Scenario` dataclass: rename `seed` → `seed_base`, add five new fields (`pattern_name`, `high_tile_magnitude`, `expected_cliff_window`, `source_citation`), add `seed(trial_index: int) -> int` method, add `__post_init__` validator (4×4 grid, palette, minimum-implied-score, magnitude match, cliff-window well-formed). |
| `nova-agent/src/nova_agent/lab/scenarios.py` | Modify | Update `fresh-start` literal for the new fields. Add three new scenarios (`snake-collapse-128`, `512-wall`, `corner-abandonment-256`). Add `MAX_MOVES: Final[int] = 50` constant. |
| `nova-agent/src/nova_agent/main.py` | Modify | `_build_io` calls `scenario.seed(0)` for live runs (trial-index 0 default for the live single-game path) instead of `scenario.seed`. |
| `nova-agent/tests/test_lab_sim.py` | Modify | Update the two existing tests that construct `Scenario(...)` directly (in `test_lab_sim.py` and `test_lab_io.py`) to populate new fields. Add eight new validator tests for `Scenario.__post_init__`. Add three sim-integration tests (one per new scenario). |
| `nova-agent/tests/test_lab_io.py` | Modify | Update the `_sim` helper's `Scenario(...)` literal to populate new fields. |
| `nova-agent/tests/test_lab_scenarios.py` | Create | New test file for SCENARIOS-corpus invariants: every scenario loads, distinct seed_bases, illusion-of-hope lower bound, max-moves upper bound, every scenario admits at least one legal move. |
| `.claude/pre-commit-checklist.md` | Modify | Per-commit per-task; reset by post-commit hook after each commit. |

**Total new tests: ~14** (8 validator + 3 sim-integration + 4 corpus-level minus 1 because the two existing tests get updates not new tests).

**Per-task discipline (applies to EVERY task):**

1. Set the env once per shell session: `export UV_PROJECT_ENVIRONMENT="$HOME/.cache/uv-envs/nova-agent"` (CLAUDE.md gotcha #1). All `uv` commands run from `nova-agent/`.
2. Quality gate trio after every implementation step that touches Python: `cd nova-agent && uv run pytest --tb=short -p no:warnings && uv run mypy && uv run ruff check`. All three must be clean before commit.
3. Before commit, re-fill `.claude/pre-commit-checklist.md` (post-commit hook resets `[x]` → `[ ]` so each commit re-fills). Pre-commit hook BLOCKS the commit if any `[ ]` is left unchecked.
4. Commit message: Conventional Commits format, body explains *why*, co-author tag `Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>`.
5. Push immediately after every commit (`git push` from the worktree).
6. After the final task in this plan, open ONE pull request — coherent unit per workflow.md PR-cadence rule.

---

## Task 1: Extend `Scenario` dataclass with new fields, validators, and `seed_base` rename

**Files:**
- Modify: `nova-agent/src/nova_agent/lab/sim.py:38-46` (the `Scenario` dataclass)
- Modify: `nova-agent/src/nova_agent/lab/scenarios.py:14-19` (the `fresh-start` literal)
- Modify: `nova-agent/src/nova_agent/main.py:60` (caller of `scenario.seed`)
- Modify: `nova-agent/tests/test_lab_sim.py` (new validator tests + update sites that construct `Scenario`)
- Modify: `nova-agent/tests/test_lab_io.py:18-26` (the `_sim` helper's `Scenario` literal)

This is the load-bearing refactor. It ends with all gate-trio checks green and the existing 140+ tests passing.

- [ ] **Step 1.1: Write failing validator tests in `tests/test_lab_sim.py`**

Append the following block to the bottom of `nova-agent/tests/test_lab_sim.py`:

```python
# ---- Scenario validator tests (per scenarios spec §3) ----


def _valid_scenario_kwargs() -> dict[str, object]:
    """Minimum-valid kwargs for a Scenario whose grid has one 8 tile.

    8 = 2^3, so minimum-implied-score = (3-1) * 8 = 16.
    """
    return {
        "id": "t",
        "initial_grid": [[8, 0, 0, 0], [0] * 4, [0] * 4, [0] * 4],
        "initial_score": 16,
        "seed_base": 1,
        "pattern_name": "test-pattern",
        "high_tile_magnitude": 8,
        "expected_cliff_window": (11, 14),
        "source_citation": "test citation",
    }


def test_scenario_rejects_non_4x4_grid() -> None:
    kwargs = _valid_scenario_kwargs()
    kwargs["initial_grid"] = [[0, 0, 0]] * 4  # 4×3, not 4×4
    with pytest.raises(ValueError, match="4x4"):
        Scenario(**kwargs)  # type: ignore[arg-type]


def test_scenario_rejects_out_of_palette_tile() -> None:
    kwargs = _valid_scenario_kwargs()
    kwargs["initial_grid"] = [[7, 0, 0, 0], [0] * 4, [0] * 4, [0] * 4]
    with pytest.raises(ValueError, match="palette"):
        Scenario(**kwargs)  # type: ignore[arg-type]


def test_scenario_rejects_initial_score_mismatch() -> None:
    kwargs = _valid_scenario_kwargs()
    kwargs["initial_score"] = 0  # board has an 8 (min-implied = 16), 0 is wrong
    with pytest.raises(ValueError, match="initial_score"):
        Scenario(**kwargs)  # type: ignore[arg-type]


def test_scenario_accepts_initial_score_matching_min_implied() -> None:
    kwargs = _valid_scenario_kwargs()
    # Already valid (initial_score=16 for one 8-tile); should construct cleanly.
    Scenario(**kwargs)  # type: ignore[arg-type]


def test_scenario_rejects_high_tile_magnitude_mismatch() -> None:
    kwargs = _valid_scenario_kwargs()
    kwargs["high_tile_magnitude"] = 16  # board's max is 8, not 16
    with pytest.raises(ValueError, match="high_tile_magnitude"):
        Scenario(**kwargs)  # type: ignore[arg-type]


def test_scenario_rejects_cliff_window_inverted() -> None:
    kwargs = _valid_scenario_kwargs()
    kwargs["expected_cliff_window"] = (14, 11)  # hi < lo
    with pytest.raises(ValueError, match="cliff_window"):
        Scenario(**kwargs)  # type: ignore[arg-type]


def test_scenario_rejects_cliff_window_zero_lower_bound() -> None:
    kwargs = _valid_scenario_kwargs()
    kwargs["expected_cliff_window"] = (0, 5)  # lower must be > 0
    with pytest.raises(ValueError, match="cliff_window"):
        Scenario(**kwargs)  # type: ignore[arg-type]


def test_scenario_seed_method_returns_seed_base_plus_trial_index() -> None:
    kwargs = _valid_scenario_kwargs()
    kwargs["seed_base"] = 1000
    s = Scenario(**kwargs)  # type: ignore[arg-type]
    assert s.seed(0) == 1000
    assert s.seed(19) == 1019
```

- [ ] **Step 1.2: Run tests to verify they fail**

Run: `cd nova-agent && export UV_PROJECT_ENVIRONMENT="$HOME/.cache/uv-envs/nova-agent" && uv run pytest tests/test_lab_sim.py -v -k scenario`

Expected: the 8 new tests FAIL (some with `TypeError` because `Scenario` doesn't accept the new kwargs; others with `AttributeError` for the missing `seed` method). Existing tests may also break because the kwargs in `_valid_scenario_kwargs` use `seed_base` not `seed` — that's expected, this commit will rename.

- [ ] **Step 1.3: Implement the dataclass extension in `nova-agent/src/nova_agent/lab/sim.py`**

Replace the existing `Scenario` dataclass (currently at `nova-agent/src/nova_agent/lab/sim.py:38-46`) with:

```python
@dataclass(frozen=True)
class Scenario:
    """Frozen, JSON-serializable starting condition for a game.

    `seed_base` is the per-scenario base seed; `seed(trial_index)` derives
    a per-trial seed for paired Carla/Bot runs per
    docs/superpowers/specs/2026-05-05-cliff-test-scenarios-design.md §2.2.

    Validators (see __post_init__) enforce: 4×4 grid, in-palette tiles,
    initial_score equals the minimum-implied-score derived from the grid,
    high_tile_magnitude matches the grid max, cliff window well-formed.
    """

    id: str
    initial_grid: list[list[int]]
    initial_score: int
    seed_base: int
    pattern_name: str
    high_tile_magnitude: int
    expected_cliff_window: tuple[int, int]
    source_citation: str

    def __post_init__(self) -> None:
        # 4×4 grid shape.
        if len(self.initial_grid) != 4 or any(len(r) != 4 for r in self.initial_grid):
            raise ValueError(f"{self.id}: initial_grid must be 4x4")
        # Tile palette (canonical 2048 powers + zero).
        valid_tiles = {0, 2, 4, 8, 16, 32, 64, 128, 256, 512, 1024, 2048}
        if any(v not in valid_tiles for r in self.initial_grid for v in r):
            raise ValueError(f"{self.id}: initial_grid contains out-of-palette tile")
        # initial_score equals minimum-implied-score derived from the grid.
        from math import log2  # local import — used only here
        derived = sum(
            int((log2(v) - 1) * v)
            for r in self.initial_grid
            for v in r
            if v > 0
        )
        if self.initial_score != derived:
            raise ValueError(
                f"{self.id}: initial_score {self.initial_score} does not match "
                f"minimum-implied-score {derived} derived from initial_grid"
            )
        # high_tile_magnitude matches grid max.
        max_tile = max((v for r in self.initial_grid for v in r), default=0)
        if self.high_tile_magnitude != max_tile:
            raise ValueError(
                f"{self.id}: high_tile_magnitude {self.high_tile_magnitude} does not "
                f"match grid max {max_tile}"
            )
        # Cliff window well-formed: 0 < lo <= hi.
        lo, hi = self.expected_cliff_window
        if not (0 < lo <= hi):
            raise ValueError(
                f"{self.id}: expected_cliff_window {self.expected_cliff_window} ill-formed"
            )

    def seed(self, trial_index: int) -> int:
        """Derive the per-trial seed: seed_base + trial_index.

        Carla trial `i` and Bot trial `i` use the same trial seed so the
        spawn schedule is identical until their decisions diverge — see
        scenarios spec §2.2.
        """
        return self.seed_base + trial_index
```

Note: the `seed` field is renamed to `seed_base`; `seed` is now a method. This is a breaking change for any caller that reads `scenario.seed` as a value. The caller updates land in steps 1.4 and 1.5.

Also update the `Game2048Sim.__init__` call site that consumes the seed if it does so via `scenario.seed`. (Reading the source: `Game2048Sim.__init__` takes `seed: int` directly as a parameter, not via the scenario, so no change required inside `Game2048Sim`.)

- [ ] **Step 1.4: Update `fresh-start` in `nova-agent/src/nova_agent/lab/scenarios.py`**

Replace the existing dict literal with:

```python
"""Phase 0.7 cliff-test scenario library.

Each Scenario is a frozen, JSON-serializable starting condition for a
Game2048Sim run. Cliff-test scenarios per
docs/superpowers/specs/2026-05-05-cliff-test-scenarios-design.md.
"""

from __future__ import annotations

from nova_agent.lab.sim import Scenario

SCENARIOS: dict[str, Scenario] = {
    "fresh-start": Scenario(
        id="fresh-start",
        initial_grid=[[0] * 4 for _ in range(4)],
        initial_score=0,
        seed_base=20260504,
        pattern_name="empty-board",
        high_tile_magnitude=0,
        expected_cliff_window=(11, 50),
        source_citation="N/A — sim-bootstrapping placeholder, not a cliff-test scenario",
    ),
}


def load(scenario_id: str) -> Scenario:
    """Return a frozen Scenario by id. Raises KeyError on unknown id."""
    if scenario_id not in SCENARIOS:
        raise KeyError(f"unknown scenario {scenario_id!r}; available: {sorted(SCENARIOS)}")
    return SCENARIOS[scenario_id]
```

Notes:
- `fresh-start` keeps its existing `seed_base=20260504` (renamed from `seed`).
- `pattern_name="empty-board"` and `high_tile_magnitude=0` are honest placeholders for the bootstrapping scenario; it is **not** a cliff-test scenario and is documented as such in `source_citation`.
- `expected_cliff_window=(11, 50)` satisfies the validator's `0 < lo <= hi` invariant; the upper bound matches `MAX_MOVES`. The corpus-level test in Task 5 will allow `fresh-start` to skip the strict `< MAX_MOVES` upper-bound check by name (or alternatively use the inclusive bound; see Task 5).

- [ ] **Step 1.5: Update the live-run caller in `nova-agent/src/nova_agent/main.py`**

Find the line at `nova-agent/src/nova_agent/main.py:60`:

```python
sim = Game2048Sim(seed=scenario.seed, scenario=scenario)
```

Replace with:

```python
# Live runs are single-game; trial_index=0 by convention. The Test
# Runner spec will override this with the real trial index per cliff-
# test trial when it lands.
sim = Game2048Sim(seed=scenario.seed(0), scenario=scenario)
```

- [ ] **Step 1.6: Update test fixtures in `nova-agent/tests/test_lab_io.py`**

Find the `_sim` helper at `nova-agent/tests/test_lab_io.py:15-26`:

```python
def _sim(grid: list[list[int]] | None = None) -> Game2048Sim:
    if grid is None:
        return Game2048Sim(seed=42)
    return Game2048Sim(
        seed=42,
        scenario=Scenario(
            id="t",
            initial_grid=grid,
            initial_score=0,
            seed=42,
        ),
    )
```

Replace with:

```python
def _sim(grid: list[list[int]] | None = None) -> Game2048Sim:
    if grid is None:
        return Game2048Sim(seed=42)
    # Compute minimum-implied-score so the validator passes.
    from math import log2
    derived_score = sum(
        int((log2(v) - 1) * v) for r in grid for v in r if v > 0
    )
    max_tile = max((v for r in grid for v in r), default=0)
    return Game2048Sim(
        seed=42,
        scenario=Scenario(
            id="t",
            initial_grid=grid,
            initial_score=derived_score,
            seed_base=42,
            pattern_name="test",
            high_tile_magnitude=max_tile,
            expected_cliff_window=(11, 14),
            source_citation="test",
        ),
    )
```

Note: the test grids passed to `_sim` (e.g., `[[2, 0, 0, 0], ...]` and `[[2, 2, 0, 0], ...]`) all have minimum-implied-scores of 0 (since `(log2(2) - 1) * 2 = 0` and a tile of 2 contributes 0 to the score). The helper correctly computes 0 in those cases. Any test that passes a grid with higher tiles will get a correct non-zero score.

- [ ] **Step 1.7: Run gate trio**

Run: `cd nova-agent && uv run pytest --tb=short -p no:warnings && uv run mypy && uv run ruff check`

Expected: all 140+ existing tests + the 8 new validator tests pass (148+ green). mypy and ruff clean.

If pytest fails: read the failure carefully. The two most likely failure modes are (a) a stale `Scenario(...)` literal in some test you haven't found yet — search `grep -rn "Scenario(" nova-agent/tests/` and update — or (b) a forgotten `scenario.seed` (no parens) reference — search `grep -rn "scenario.seed[^(]" nova-agent/`.

If mypy fails: most likely the `expected_cliff_window` tuple needs `tuple[int, int]` not `tuple[int, ...]`. The dataclass field annotation already says `tuple[int, int]`; ensure no callers pass a list or wrong-length tuple.

If ruff fails: most likely the local `from math import log2` in `__post_init__` needs `# noqa: PLC0415` or the import gets hoisted to top. Hoist to top of file: `from math import log2` near the existing imports.

- [ ] **Step 1.8: Re-fill the pre-commit checklist**

Open `.claude/pre-commit-checklist.md` and check each box, with annotations. Sample contents:

```markdown
## Branch + scope
- [x] On feature branch `claude/practical-swanson-4b6468`, not `main`
- [x] `git diff --cached --stat` reviewed — Scenario dataclass extension + caller migrations
- [x] Atomic commit — single logical change: extend Scenario contract per spec

## Verification
- [x] `git diff --cached` scanned for secrets — no env values / API keys / tokens
- [x] `nova-agent/` — pytest + mypy + ruff all green (gate trio passed)
- [x] `nova-viewer/` not touched — N/A vitest/tsc/eslint
- [x] Docs / config — none touched

## Review
- [x] `/review` dispatched — N/A: REVIEW.md taxonomy `N/A: refactor` (rename + dataclass extension; covered by validator tests)
- [x] `code-reviewer` subagent — N/A; auto Layer 1.5 pre-push hook covers
- [x] `security-reviewer` — N/A: no secrets / env / LLM / bus paths

## Documentation
- [x] LESSONS.md — N/A this commit
- [x] CLAUDE.md "Common gotchas" — N/A
- [x] ARCHITECTURE.md — N/A
- [x] New ADR — N/A; spec implements ADR-0007 at the dataclass layer

## Commit message
- [x] Conventional Commits format: `feat(lab): extend Scenario dataclass with cliff-test fields`
- [x] Body explains why — see commit body
- [x] Co-author tag present
```

- [ ] **Step 1.9: Stage and commit**

```bash
git add nova-agent/src/nova_agent/lab/sim.py \
        nova-agent/src/nova_agent/lab/scenarios.py \
        nova-agent/src/nova_agent/main.py \
        nova-agent/tests/test_lab_sim.py \
        nova-agent/tests/test_lab_io.py \
        .claude/pre-commit-checklist.md

git diff --cached --stat
```

Expected stat: 6 files changed. Inspect for unexpected hunks.

```bash
git commit -m "$(cat <<'EOF'
feat(lab): extend Scenario dataclass with cliff-test fields

Renames the `seed` field to `seed_base` and adds a `seed(trial_index)`
method for paired Carla/Bot per-trial seed derivation. Adds five new
fields per the cliff-test scenarios spec — pattern_name,
high_tile_magnitude, expected_cliff_window, source_citation — and a
__post_init__ validator that enforces 4×4 shape, in-palette tiles,
the minimum-implied-score formula, magnitude match, and cliff-window
well-formedness.

Migrates the fresh-start scenario, the live-run main.py caller, and
the test_lab_io.py fixture to the new contract. Covered by 8 new
validator tests; existing 140+ tests stay green.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

If the pre-commit hook reports an unchecked box, re-fill the checklist and re-commit (do **not** `--amend`; the commit didn't happen — re-stage if `git status` shows clean working tree, otherwise re-commit fresh).

- [ ] **Step 1.10: Push**

```bash
git push
```

Pre-push hook (Layer 1.5, Sonnet) will auto-review the commit. Doc-and-refactor-with-tests usually passes; if a critical finding blocks the push, address it and re-push.

---

## Task 2: Add `snake-collapse-128` scenario

**Files:**
- Modify: `nova-agent/src/nova_agent/lab/scenarios.py` (append the scenario to the `SCENARIOS` dict)
- Modify: `nova-agent/tests/test_lab_sim.py` (add the sim-integration test)

- [ ] **Step 2.1: Write the failing sim-integration test**

Append to `nova-agent/tests/test_lab_sim.py`:

```python
# ---- Per-cliff-scenario sim integration ----


def test_snake_collapse_128_loads_into_sim() -> None:
    from nova_agent.lab.scenarios import SCENARIOS
    s = SCENARIOS["snake-collapse-128"]
    sim = Game2048Sim(seed=s.seed(0), scenario=s)
    assert sim.board.grid == s.initial_grid
    assert sim.board.score == s.initial_score
    assert sim.board.score == 1308  # explicit cross-check of the formula
    assert s.high_tile_magnitude == 128
```

- [ ] **Step 2.2: Run the test to verify it fails**

Run: `cd nova-agent && uv run pytest tests/test_lab_sim.py::test_snake_collapse_128_loads_into_sim -v`

Expected: `KeyError: 'snake-collapse-128'`.

- [ ] **Step 2.3: Add the scenario in `nova-agent/src/nova_agent/lab/scenarios.py`**

Append to the `SCENARIOS` dict literal (after `fresh-start`):

```python
    "snake-collapse-128": Scenario(
        id="snake-collapse-128",
        initial_grid=[
            [0, 0, 0, 2],
            [4, 2, 4, 8],
            [0, 4, 16, 32],
            [2, 8, 64, 128],
        ],
        initial_score=1308,
        seed_base=20260505001,
        pattern_name="snake-collapse",
        high_tile_magnitude=128,
        expected_cliff_window=(11, 16),
        source_citation=(
            "2048 strategy guides describing snake-formation collapse "
            "(e.g. Hak.is 'How to beat 2048' walkthrough; r/2048 community "
            "discussions of snake-stall failure). URL pinning deferred "
            "per scenarios spec §9."
        ),
    ),
```

- [ ] **Step 2.4: Run gate trio**

Run: `cd nova-agent && uv run pytest --tb=short -p no:warnings && uv run mypy && uv run ruff check`

Expected: all green. The new test passes; the validator-passes-on-construction is implicitly tested by the dict literal evaluating without raise at import time (Python evaluates `Scenario(...)` literals on module import, so any validator failure surfaces as `ImportError` at test collection time).

- [ ] **Step 2.5: Re-fill checklist, commit, push**

Checklist annotation: `feat(scenarios): add snake-collapse-128 cliff-test scenario`. Body: cite spec §4.1.

```bash
git add nova-agent/src/nova_agent/lab/scenarios.py \
        nova-agent/tests/test_lab_sim.py \
        .claude/pre-commit-checklist.md
git commit -m "$(cat <<'EOF'
feat(scenarios): add snake-collapse-128 cliff-test scenario

First of three cliff-test scenarios per the scenarios spec §4.1.
Snake formation anchored bottom-right with descending tiles 128 →
64 → 32 → 16 → 8 → 4 → 2; near-cliff state where the misaligned
bottom-left 2 plus spawn pressure forces a snake-breaking swipe.
Magnitude 128 is the modal casual-snake reach per the spec's
persona-calibrated-magnitude principle.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
git push
```

---

## Task 3: Add `512-wall` scenario

**Files:**
- Modify: `nova-agent/src/nova_agent/lab/scenarios.py`
- Modify: `nova-agent/tests/test_lab_sim.py`

- [ ] **Step 3.1: Write the failing test**

Append to `nova-agent/tests/test_lab_sim.py`:

```python
def test_512_wall_loads_into_sim() -> None:
    from nova_agent.lab.scenarios import SCENARIOS
    s = SCENARIOS["512-wall"]
    sim = Game2048Sim(seed=s.seed(0), scenario=s)
    assert sim.board.grid == s.initial_grid
    assert sim.board.score == s.initial_score
    assert sim.board.score == 8152
    assert s.high_tile_magnitude == 512
```

- [ ] **Step 3.2: Run, verify fail**

Run: `cd nova-agent && uv run pytest tests/test_lab_sim.py::test_512_wall_loads_into_sim -v`. Expected `KeyError`.

- [ ] **Step 3.3: Add the scenario in `nova-agent/src/nova_agent/lab/scenarios.py`**

Append to `SCENARIOS`:

```python
    "512-wall": Scenario(
        id="512-wall",
        initial_grid=[
            [0, 4, 8, 2],
            [4, 8, 16, 32],
            [8, 16, 32, 128],
            [256, 64, 128, 512],
        ],
        initial_score=8152,
        seed_base=20260505002,
        pattern_name="high-tile-wall",
        high_tile_magnitude=512,
        expected_cliff_window=(12, 17),
        source_citation=(
            "2048 strategy guides describing the 1024-wall pattern "
            "(e.g. 2048 wiki, speedrun community guides on stack-blocking "
            "failures). Spec adapts the cited 1024-wall pattern to 512 "
            "for Casual-Carla persona-fidelity per scenarios spec §2.5; "
            "URL pinning deferred per scenarios spec §9."
        ),
    ),
```

- [ ] **Step 3.4: Run gate trio**

Same as Task 2.4. Expect green.

- [ ] **Step 3.5: Re-fill checklist, commit, push**

Subject: `feat(scenarios): add 512-wall cliff-test scenario`.

```bash
git add nova-agent/src/nova_agent/lab/scenarios.py \
        nova-agent/tests/test_lab_sim.py \
        .claude/pre-commit-checklist.md
git commit -m "$(cat <<'EOF'
feat(scenarios): add 512-wall cliff-test scenario

Second of three cliff-test scenarios per the scenarios spec §4.2.
Instantiates the methodology's 1024-wall pattern at the 512
magnitude — Casual-Carla persona-fidelity per the spec's
persona-calibrated-magnitude principle. The 512 anchored
bottom-right is blocked by a misaligned 256+128 stack; casual play
fragments the merge path through ~12-17 moves before the 256→512
merge becomes provably unreachable.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
git push
```

---

## Task 4: Add `corner-abandonment-256` scenario

**Files:**
- Modify: `nova-agent/src/nova_agent/lab/scenarios.py`
- Modify: `nova-agent/tests/test_lab_sim.py`

- [ ] **Step 4.1: Write the failing test**

Append to `nova-agent/tests/test_lab_sim.py`:

```python
def test_corner_abandonment_256_loads_into_sim() -> None:
    from nova_agent.lab.scenarios import SCENARIOS
    s = SCENARIOS["corner-abandonment-256"]
    sim = Game2048Sim(seed=s.seed(0), scenario=s)
    assert sim.board.grid == s.initial_grid
    assert sim.board.score == s.initial_score
    assert sim.board.score == 4364
    assert s.high_tile_magnitude == 256
```

- [ ] **Step 4.2: Run, verify fail**

`cd nova-agent && uv run pytest tests/test_lab_sim.py::test_corner_abandonment_256_loads_into_sim -v`. Expected `KeyError`.

- [ ] **Step 4.3: Add the scenario**

Append to `SCENARIOS`:

```python
    "corner-abandonment-256": Scenario(
        id="corner-abandonment-256",
        initial_grid=[
            [0, 4, 8, 2],
            [4, 8, 16, 32],
            [16, 32, 64, 128],
            [64, 256, 128, 4],
        ],
        initial_score=4364,
        seed_base=20260505003,
        pattern_name="corner-abandonment",
        high_tile_magnitude=256,
        expected_cliff_window=(12, 18),
        source_citation=(
            "r/2048 community posts on corner-abandonment failures and "
            "strategy walkthroughs describing high-tile mobility "
            "consequences (e.g. the 'never let the high tile leave the "
            "corner' rule and cascade-failure mode). URL pinning "
            "deferred per scenarios spec §9."
        ),
    ),
```

- [ ] **Step 4.4: Run gate trio**

Expect green.

- [ ] **Step 4.5: Re-fill checklist, commit, push**

Subject: `feat(scenarios): add corner-abandonment-256 cliff-test scenario`.

```bash
git add nova-agent/src/nova_agent/lab/scenarios.py \
        nova-agent/tests/test_lab_sim.py \
        .claude/pre-commit-checklist.md
git commit -m "$(cat <<'EOF'
feat(scenarios): add corner-abandonment-256 cliff-test scenario

Third of three cliff-test scenarios per the scenarios spec §4.3.
Casual player anchored a 256 in the bottom-left corner; one bad
upward swipe pushed it inward, leaving 64 in the corner and 256
dislocated. The two 128s on the diagonal cannot merge; recovery
requires 12-18 moves before mid-board chaos forecloses. Magnitude
256 matches the modal casual-player corner-abandonment failure
per the spec's persona-calibrated-magnitude principle.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
git push
```

---

## Task 5: Add `MAX_MOVES` constant + corpus-level invariant tests

**Files:**
- Modify: `nova-agent/src/nova_agent/lab/scenarios.py` (add `MAX_MOVES` constant)
- Create: `nova-agent/tests/test_lab_scenarios.py` (corpus tests)

- [ ] **Step 5.1: Write the failing corpus tests**

Create `nova-agent/tests/test_lab_scenarios.py`:

```python
"""Cliff-test scenario corpus invariants.

Validates the SCENARIOS dict against the cross-scenario invariants
documented in docs/superpowers/specs/2026-05-05-cliff-test-scenarios-design.md
§7.2 and §7.3.
"""

from __future__ import annotations

from nova_agent.action.adb import SwipeDirection
from nova_agent.lab.scenarios import MAX_MOVES, SCENARIOS
from nova_agent.lab.sim import Game2048Sim

# Scenarios that are NOT cliff-test scenarios and skip cliff-specific
# invariants (the illusion-of-hope lower bound + max-moves upper bound).
_NON_CLIFF_SCENARIOS: frozenset[str] = frozenset({"fresh-start"})

_CLIFF_SCENARIO_IDS: tuple[str, ...] = (
    "snake-collapse-128",
    "512-wall",
    "corner-abandonment-256",
)


def test_max_moves_is_50() -> None:
    assert MAX_MOVES == 50


def test_all_cliff_scenarios_present() -> None:
    for sid in _CLIFF_SCENARIO_IDS:
        assert sid in SCENARIOS, f"missing cliff scenario {sid!r}"


def test_all_scenarios_have_distinct_seed_base() -> None:
    seed_bases = [s.seed_base for s in SCENARIOS.values()]
    assert len(seed_bases) == len(set(seed_bases)), (
        f"duplicate seed_base in SCENARIOS: {seed_bases}"
    )


def test_cliff_scenarios_satisfy_illusion_of_hope_lower_bound() -> None:
    # Per spec §2.1: 10-15 prior-move buffer before gridlock means
    # cliff manifests no earlier than move 11.
    for sid in _CLIFF_SCENARIO_IDS:
        s = SCENARIOS[sid]
        lo, _hi = s.expected_cliff_window
        assert lo >= 11, (
            f"{sid}: expected_cliff_window lower bound {lo} violates "
            f"illusion-of-hope (must be >= 11)"
        )


def test_cliff_scenarios_satisfy_max_moves_upper_bound() -> None:
    for sid in _CLIFF_SCENARIO_IDS:
        s = SCENARIOS[sid]
        _lo, hi = s.expected_cliff_window
        assert hi < MAX_MOVES, (
            f"{sid}: expected_cliff_window upper bound {hi} violates "
            f"max_moves cap (must be < {MAX_MOVES})"
        )


def test_every_scenario_admits_at_least_one_legal_move() -> None:
    for sid, s in SCENARIOS.items():
        sim = Game2048Sim(seed=s.seed(0), scenario=s)
        before = [row[:] for row in sim.board.grid]
        legal_directions = []
        for direction in (
            SwipeDirection.UP,
            SwipeDirection.DOWN,
            SwipeDirection.LEFT,
            SwipeDirection.RIGHT,
        ):
            test_sim = Game2048Sim(seed=s.seed(0), scenario=s)
            if test_sim.apply_move(direction):
                legal_directions.append(direction)
        assert legal_directions, (
            f"{sid}: initial state admits no legal move; before={before}"
        )


def test_non_cliff_scenarios_documented() -> None:
    """Catch authoring errors where a cliff scenario gets misclassified."""
    documented = _NON_CLIFF_SCENARIOS | set(_CLIFF_SCENARIO_IDS)
    actual = set(SCENARIOS.keys())
    assert actual == documented, (
        f"SCENARIOS contains {actual - documented} not in either "
        f"_NON_CLIFF_SCENARIOS or _CLIFF_SCENARIO_IDS — classify it "
        f"in this test file"
    )
```

- [ ] **Step 5.2: Run, verify fail**

Run: `cd nova-agent && uv run pytest tests/test_lab_scenarios.py -v`

Expected: `ImportError: cannot import name 'MAX_MOVES' from 'nova_agent.lab.scenarios'`. The other tests don't run because import fails first.

- [ ] **Step 5.3: Add `MAX_MOVES` to `nova-agent/src/nova_agent/lab/scenarios.py`**

At the top of `nova-agent/src/nova_agent/lab/scenarios.py` (above the `SCENARIOS` dict), add:

```python
from typing import Final

# Per cliff-test scenarios spec §2.8: hard cap of 50 moves per trial.
# Trials reaching this cap right-censor (recorded but flagged as
# scenario-invalidation evidence). Calibration: ~3× the upper safety
# margin above the maximum expected_cliff_window upper bound (~17).
MAX_MOVES: Final[int] = 50
```

The existing `from __future__ import annotations` line at the top of the file should remain. The `from typing import Final` import goes below it.

- [ ] **Step 5.4: Run the gate trio**

Run: `cd nova-agent && uv run pytest --tb=short -p no:warnings && uv run mypy && uv run ruff check`

Expected: all green. The 7 new corpus tests pass.

If `test_every_scenario_admits_at_least_one_legal_move` fails for any cliff scenario: the grid is genuinely game-over at move 0, which means the spec's grid is wrong. Re-author the grid. This is a real signal, not a test bug.

If `test_cliff_scenarios_satisfy_max_moves_upper_bound` fails: a cliff window's upper bound was set ≥ 50. Tighten the window or raise `MAX_MOVES` (but raising `MAX_MOVES` requires a spec amendment; tighten the window instead).

- [ ] **Step 5.5: Re-fill checklist, commit, push**

Subject: `feat(scenarios): add MAX_MOVES cap and corpus invariant tests`.

```bash
git add nova-agent/src/nova_agent/lab/scenarios.py \
        nova-agent/tests/test_lab_scenarios.py \
        .claude/pre-commit-checklist.md
git commit -m "$(cat <<'EOF'
feat(scenarios): add MAX_MOVES cap and corpus invariant tests

Adds the MAX_MOVES = 50 module-level constant per scenarios spec §2.8
and the cross-scenario corpus invariants per spec §7.2: distinct
seed_bases, illusion-of-hope lower bound (cliff_window[0] >= 11) for
cliff scenarios, max-moves upper bound (cliff_window[1] < MAX_MOVES)
for cliff scenarios, every scenario admits at least one legal move at
move 0 (catches authoring errors that would game-over before any
agent action).

Closes the implementation surface for the cliff-test scenarios spec.
The spec's pilot calibration (§7.4) is a follow-up gate before the
real N=20 run, requiring the Test Runner spec to land first.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
git push
```

---

## Task 6 (conditional): LESSONS.md sweep

**Files:**
- Modify: `LESSONS.md` (only if a non-obvious surprise surfaced during implementation)

If during Tasks 1-5 you discovered something surprising — e.g., a `Scenario` validator that rejected a board the human didn't expect, an mypy error that took 15+ minutes to debug, a renamed-field migration that touched a file not anticipated in this plan — capture it in `LESSONS.md` per the `/lessons-add` workflow.

If nothing surprised you, skip this task entirely. Note "Task 6 — N/A, no surprises" on the PR description.

---

## After Task 5: open the PR

Per workflow.md PR-cadence rule: this plan's commits form one coherent unit ("Phase 0.7 cliff-test scenarios + dataclass extension"). Open ONE PR after Task 5 lands.

```bash
gh pr create --title "feat(lab): cliff-test scenarios + Scenario dataclass extension" --body "$(cat <<'EOF'
## Summary

Implements the cliff-test scenarios spec (`docs/superpowers/specs/2026-05-05-cliff-test-scenarios-design.md`):

- Extended `Scenario` dataclass with five new fields (`pattern_name`, `high_tile_magnitude`, `expected_cliff_window`, `source_citation`) and renamed `seed` → `seed_base` with a paired-trial-seed `seed(trial_index)` method. `__post_init__` validator enforces 4×4 shape, in-palette tiles, the minimum-implied-score formula, magnitude match, and cliff-window well-formedness.
- Added three cliff-test scenarios per spec §4: `snake-collapse-128`, `512-wall`, `corner-abandonment-256`.
- Added `MAX_MOVES = 50` constant and corpus-level invariant tests.

Six rounds of red-team review pinned the design. See spec §2 for the decision rationale and §10 for cross-references.

## Test plan

- [ ] `cd nova-agent && uv run pytest --tb=short -p no:warnings` — all (140 + ~14 new) tests green
- [ ] `cd nova-agent && uv run mypy` — strict mode clean
- [ ] `cd nova-agent && uv run ruff check` — clean
- [ ] CI green on the branch
- [ ] Inspect each scenario grid in `nova-agent/src/nova_agent/lab/scenarios.py` against spec §4 — boards match the cited patterns and the validator-derived `initial_score` is correct
- [ ] Manual smoke (optional, requires emulator): `NOVA_IO_SOURCE=sim NOVA_SIM_SCENARIO=snake-collapse-128 uv run nova` — agent boots on the new scenario without errors

## Out of scope (handled by follow-up specs)

- The Test Runner implementation
- The Baseline Bot architectural choice (LLM vs heuristic)
- URL-pinned `source_citation` strings (deferred per spec §9)
- Pilot calibration (requires Baseline Bot spec; per spec §7.4)

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

The Layer 2 PR review hook (`claude-code-action`, Opus) auto-runs on PR open. Wait for its findings before merging.

---

## Self-review checklist (run after writing this plan)

This is a checklist for the plan author, not the executor — completed before the plan is handed off.

- **Spec coverage:** every requirement in the spec has at least one task that implements it.
  - §3 dataclass extension → Task 1
  - §4.1 snake-collapse-128 → Task 2
  - §4.2 512-wall → Task 3
  - §4.3 corner-abandonment-256 → Task 4
  - §2.8 MAX_MOVES → Task 5
  - §7.1, §7.2, §7.3 tests → Tasks 1, 2, 3, 4, 5
  - §7.4 pilot calibration → out-of-scope, noted in plan header
  - §9 URL pinning → out-of-scope, noted in plan header
- **Placeholder scan:** no "TBD", no "TODO", no "implement later", no unspecified assertions, no "similar to Task N" references; every code block contains the actual code; every test contains the actual assertions.
- **Type consistency:** field names match across all tasks (`seed_base`, `pattern_name`, `high_tile_magnitude`, `expected_cliff_window`, `source_citation`); the `seed(trial_index: int) -> int` method signature is consistent across Task 1 (definition) and Tasks 2-5 (callers); `MAX_MOVES` is defined in Task 5 and referenced consistently.
