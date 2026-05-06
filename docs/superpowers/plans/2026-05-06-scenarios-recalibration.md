# Phase 0.7 Cliff-Test Scenarios — Recalibration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship the three recalibrated cliff-test scenario grids (per `docs/superpowers/specs/2026-05-06-scenarios-recalibration-design.md` §3), keep all existing tests green, run an N=5 pilot at production tier with Sonnet 4.6 ToT, and adjudicate the four §5 acceptance criteria to authorise (or block) the real N=20 run.

**Architecture:** Data-only change to three `Scenario(...)` literals in `nova_agent/lab/scenarios.py`. Existing schema invariants (`Scenario.__post_init__` + `test_lab_scenarios.py`) and existing scenario-agnostic cliff-test tests cover the new grids automatically. One stale inline comment in `test_cliff_test_helpers.py` needs an update. After the impl commit, the operator runs the cliff-test CLI in pilot mode and adjudicates the §5 acceptance criteria from the resulting CSV.

**Tech Stack:** Python 3.14, `uv` (with `UV_PROJECT_ENVIRONMENT=$HOME/.cache/uv-envs/nova-agent`), pytest, mypy strict, ruff, the existing `cliff-test` CLI (entry point in `nova-agent/src/nova_agent/lab/cliff_test.py`). No new dependencies.

---

## File Structure

**Modify:**

- `nova-agent/src/nova_agent/lab/scenarios.py` — three `Scenario(...)` literal updates: `initial_grid`, `initial_score`, `expected_cliff_window`. The `seed_base`, `pattern_name`, `high_tile_magnitude`, and `source_citation` fields are unchanged on every scenario.
- `nova-agent/tests/test_lab_scenarios.py` — add three regression tests pinning the spec §3 grids/scores/windows. Existing invariant tests stay unchanged.
- `nova-agent/tests/test_cliff_test_helpers.py` — line 232 inline comment update (the old comment said "snake-collapse-128 initial grid has empty cells in the top row"; the new snake grid has 0 empty cells; UP is still legal via the col-3 4+4 merge).

**Create:**

- (Pilot only) `nova-agent/runs/2026-05-06-pilot-recalibrated/pilot_results/cliff_test_results.csv` — pilot output, gitignored.

**Reference:**

- `docs/superpowers/specs/2026-05-06-scenarios-recalibration-design.md` (commit `13d14eb`) — the source-of-truth matrices, scores, windows, and §5 acceptance criteria.
- `docs/superpowers/specs/2026-05-05-cliff-test-scenarios-design.md` — the framework (unchanged).

---

## Task 1: Recalibrate the three scenarios (atomic TDD commit)

**Files:**
- Test: `nova-agent/tests/test_lab_scenarios.py` (extend with regression tests)
- Modify: `nova-agent/src/nova_agent/lab/scenarios.py`
- Modify: `nova-agent/tests/test_cliff_test_helpers.py:232`

This is a single atomic commit — tests + impl + comment fix in one logical change.

- [ ] **Step 1.1: Confirm worktree state and env**

```bash
cd /Users/idohoresh/Desktop/a/.claude/worktrees/practical-swanson-4b6468
git status --short
git branch --show-current
export UV_PROJECT_ENVIRONMENT="$HOME/.cache/uv-envs/nova-agent"
```

Expected: clean working tree (post-`13d14eb`), branch `claude/practical-swanson-4b6468`, env var exported.

- [ ] **Step 1.2: Add three failing regression tests**

Append to `nova-agent/tests/test_lab_scenarios.py` (after the existing tests):

```python
# ---------------------------------------------------------------------------
# Recalibration pins (2026-05-06)
#
# Per docs/superpowers/specs/2026-05-06-scenarios-recalibration-design.md §3,
# the three cliff scenarios were recalibrated after the 2026-05-06 pilot
# exposed §7.4 calibration failures. These tests pin the recalibrated values
# so a future revert is caught.
# ---------------------------------------------------------------------------


def test_corner_abandonment_recalibrated_2026_05_06() -> None:
    s = SCENARIOS["corner-abandonment-256"]
    assert s.initial_grid == [
        [0, 4, 0, 0],
        [4, 8, 4, 2],
        [0, 16, 8, 128],
        [64, 256, 128, 32],
    ]
    assert s.initial_score == 3868
    assert s.expected_cliff_window == (12, 17)
    assert s.high_tile_magnitude == 256
    assert s.pattern_name == "corner-abandonment"


def test_snake_collapse_recalibrated_2026_05_06() -> None:
    s = SCENARIOS["snake-collapse-128"]
    assert s.initial_grid == [
        [16, 4, 8, 16],
        [4, 32, 4, 4],
        [8, 4, 32, 4],
        [2, 8, 64, 128],
    ]
    assert s.initial_score == 1512
    assert s.expected_cliff_window == (11, 16)
    assert s.high_tile_magnitude == 128
    assert s.pattern_name == "snake-collapse"


def test_512_wall_recalibrated_2026_05_06() -> None:
    s = SCENARIOS["512-wall"]
    assert s.initial_grid == [
        [0, 4, 8, 0],
        [4, 8, 16, 32],
        [8, 16, 32, 128],
        [256, 32, 128, 512],
    ]
    assert s.initial_score == 7960
    assert s.expected_cliff_window == (12, 17)
    assert s.high_tile_magnitude == 512
    assert s.pattern_name == "high-tile-wall"
```

- [ ] **Step 1.3: Run the three new tests — verify they FAIL**

```bash
cd nova-agent
uv run pytest tests/test_lab_scenarios.py::test_corner_abandonment_recalibrated_2026_05_06 tests/test_lab_scenarios.py::test_snake_collapse_recalibrated_2026_05_06 tests/test_lab_scenarios.py::test_512_wall_recalibrated_2026_05_06 -v
```

Expected: 3 FAILED. Each fails on the `initial_grid` or `initial_score` mismatch (current scenarios.py still has the pre-recalibration values).

- [ ] **Step 1.4: Apply scenarios.py edits — corner-abandonment-256**

Replace the `corner-abandonment-256` literal (currently at lines ~72–92) in `nova-agent/src/nova_agent/lab/scenarios.py`. Old `initial_grid` / `initial_score` / `expected_cliff_window` replaced; `seed_base` / `pattern_name` / `high_tile_magnitude` / `source_citation` preserved.

Old:

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

New:

```python
    "corner-abandonment-256": Scenario(
        id="corner-abandonment-256",
        initial_grid=[
            [0, 4, 0, 0],
            [4, 8, 4, 2],
            [0, 16, 8, 128],
            [64, 256, 128, 32],
        ],
        initial_score=3868,
        seed_base=20260505003,
        pattern_name="corner-abandonment",
        high_tile_magnitude=256,
        expected_cliff_window=(12, 17),
        source_citation=(
            "r/2048 community posts on corner-abandonment failures and "
            "strategy walkthroughs describing high-tile mobility "
            "consequences (e.g. the 'never let the high tile leave the "
            "corner' rule and cascade-failure mode). URL pinning "
            "deferred per scenarios spec §9."
        ),
    ),
```

- [ ] **Step 1.5: Apply scenarios.py edits — snake-collapse-128**

Replace the `snake-collapse-128` literal (currently at lines ~31–50) in `nova-agent/src/nova_agent/lab/scenarios.py`.

Old:

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

New:

```python
    "snake-collapse-128": Scenario(
        id="snake-collapse-128",
        initial_grid=[
            [16, 4, 8, 16],
            [4, 32, 4, 4],
            [8, 4, 32, 4],
            [2, 8, 64, 128],
        ],
        initial_score=1512,
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

- [ ] **Step 1.6: Apply scenarios.py edits — 512-wall**

Replace the `512-wall` literal (currently at lines ~51–71) in `nova-agent/src/nova_agent/lab/scenarios.py`.

Old:

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

New:

```python
    "512-wall": Scenario(
        id="512-wall",
        initial_grid=[
            [0, 4, 8, 0],
            [4, 8, 16, 32],
            [8, 16, 32, 128],
            [256, 32, 128, 512],
        ],
        initial_score=7960,
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

- [ ] **Step 1.7: Update the stale comment in test_cliff_test_helpers.py**

In `nova-agent/tests/test_cliff_test_helpers.py`, lines 232–233 contain a stale comment about snake-collapse-128 having "empty cells in the top row." The new snake grid is fully packed; UP is still legal because of the col-3 `4+4 → 8` merge. Update the comment.

Old:

```python
        # snake-collapse-128 initial grid has empty cells in the top row;
        # swipe_up compacts tiles upward and is legal on this starting board.
        applied = _apply_with_tiebreak(io, "swipe_up", board)
```

New:

```python
        # snake-collapse-128 initial grid is fully packed but UP is legal
        # via the col-3 4+4 merge (per spec recalibration 2026-05-06 §3.2).
        applied = _apply_with_tiebreak(io, "swipe_up", board)
```

- [ ] **Step 1.8: Run the three regression tests — verify they PASS**

```bash
cd nova-agent
uv run pytest tests/test_lab_scenarios.py::test_corner_abandonment_recalibrated_2026_05_06 tests/test_lab_scenarios.py::test_snake_collapse_recalibrated_2026_05_06 tests/test_lab_scenarios.py::test_512_wall_recalibrated_2026_05_06 -v
```

Expected: 3 PASSED.

- [ ] **Step 1.9: Run the full test_lab_scenarios.py — verify no other test breaks**

```bash
cd nova-agent
uv run pytest tests/test_lab_scenarios.py -v
```

Expected: all PASSED (existing invariant tests + 3 new regression tests).

- [ ] **Step 1.10: Run the full /check-agent trio**

```bash
cd nova-agent
uv run pytest --tb=short -p no:warnings && uv run mypy && uv run ruff check
```

Expected: pytest PASS (full suite, currently ~270 tests), mypy strict clean, ruff clean.

If any of the three stages fail: do not proceed. Investigate root cause. Common pitfalls:
- A cliff-test helper test that depends on snake-collapse's specific topology beyond the line-232 comment (none expected, but check the failure trace).
- Mypy complaining about a literal type mismatch (unlikely; Scenario is a frozen dataclass with explicit types).
- Ruff complaining about whitespace or line length in the new test additions.

- [ ] **Step 1.11: Update pre-commit checklist for the new commit**

Edit `.claude/pre-commit-checklist.md` body to describe this commit (the post-commit hook reset boxes after `13d14eb`; body persists from prior). Set:

```markdown
# Pre-Commit Checklist

> Hook-enforced: any unchecked-box line blocks the commit. Mark `[x]` when done; for N/A items use `[x] N/A: <reason>`. Silent skip is forbidden. Post-commit hook auto-resets boxes to unchecked for the next commit.

- [x] **Branch + scope** — on `claude/practical-swanson-4b6468`; atomic unit: recalibrate 3 cliff-test scenario grids per spec 2026-05-06-scenarios-recalibration-design.md §3 + 3 regression tests pinning the new values + 1 stale-comment fix in test_cliff_test_helpers.py (3 files: scenarios.py, test_lab_scenarios.py, test_cliff_test_helpers.py; ≈+50/-20 lines).
- [x] **Verification** — `git diff --cached` scanned (no secrets, no PII); /check-agent trio clean (full pytest suite green including 3 new regression tests; mypy strict clean; ruff clean).
- [x] **Review** — N/A: mechanical data update in lab fixtures + corresponding regression tests; no cognitive-layer code touched (per `feedback_subagent_dispatch_selectivity` policy: lab/scenarios is not on the LLM/bus/secrets surface that warrants Opus-tier review). Layer 1.5 pre-push hook will run code-review at push time as backstop.
- [x] **Documentation** — design rationale lives in spec 2026-05-06-scenarios-recalibration-design.md (commit 13d14eb); the three regression tests reference the spec section in their docstring; the stale comment in test_cliff_test_helpers.py is updated to point at spec §3.2.
- [x] **Commit message** — `fix(lab): recalibrate cliff-test scenario grids per spec 2026-05-06`; body explains pilot-driven recalibration scope (3 grids + 3 pins + 1 comment fix), spec reference, scope-boundary (no framework / ADR change), co-author tag.
```

- [ ] **Step 1.12: Stage, secret-scan, commit, push**

```bash
cd /Users/idohoresh/Desktop/a/.claude/worktrees/practical-swanson-4b6468
git add nova-agent/src/nova_agent/lab/scenarios.py \
        nova-agent/tests/test_lab_scenarios.py \
        nova-agent/tests/test_cliff_test_helpers.py \
        .claude/pre-commit-checklist.md
git diff --cached --stat
git diff --cached | grep -E -i '(api[_-]?key|secret|token|password|bearer|sk-[a-z0-9]+)' || echo "no-secret-patterns-matched"
git commit -m "$(cat <<'EOF'
fix(lab): recalibrate cliff-test scenario grids per spec 2026-05-06

2026-05-06 pilot exposed §7.4 calibration failures: corner-abandonment-256
killed Bot at move 4-5 (window 12-17), snake-collapse-128 hit cap 3/5
(>2/20 broken threshold), 512-wall mixed (1/5 in-window, 1/5 cap). Carla
t_predicts ≈ 0-1 on corner+512 (fast-reaction failure) while snake's
median = 6 worked.

Per spec docs/superpowers/specs/2026-05-06-scenarios-recalibration-design.md
§3 (commit 13d14eb), apply data-driven per-scenario fixes:

- corner-abandonment-256: 4 empty cells (was 1), 4 legal moves at start,
  diagonal-128 trap preserved; window (12,17) (was (12,18)).
- snake-collapse-128: 0 empty cells (was 3) + diagonal 32 blockers;
  broken-snake cue preserved (Carla median=6 untouched); window unchanged.
- 512-wall: upper-right relief cell, wall tightened ((3,1)=32 was 64);
  window unchanged.

Three regression tests pin the new values per spec §3. One stale comment
in test_cliff_test_helpers.py updated (snake top row no longer empty).

Framework unchanged. No ADR.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
git push origin claude/practical-swanson-4b6468
```

Expected: pre-commit hooks pass (gitleaks, trim whitespace, conventional commit, checklist). Push succeeds.

If pre-commit fails: read the hook output, fix the underlying issue, re-stage, create a NEW commit (never `--amend` or `--no-verify`).

---

## Task 2: Re-calibration pilot (operator-driven; agent prep + monitor)

**Files:**
- Output: `nova-agent/runs/2026-05-06-pilot-recalibrated/pilot_results/cliff_test_results.csv` (gitignored).

This task runs a real LLM call sequence (~$5–7 expected per spec §5). It is not automatic; the operator authorises and runs. The agent prepares the environment and monitors completion.

- [ ] **Step 2.1: Pre-flight environment check**

```bash
cd /Users/idohoresh/Desktop/a/.claude/worktrees/practical-swanson-4b6468
export UV_PROJECT_ENVIRONMENT="$HOME/.cache/uv-envs/nova-agent"
cd nova-agent
# Verify .env presence + Anthropic key (cliff-test ToT path requires it)
test -f .env && grep -E '^ANTHROPIC_API_KEY=.+' .env >/dev/null && echo "anthropic key set" || echo "MISSING: anthropic key in .env"
grep -E '^GEMINI_API_KEY=.+' .env >/dev/null && echo "gemini key set" || echo "MISSING: gemini key in .env"
# Confirm no env-shadow on Anthropic key (gotcha #3)
printenv | grep -E '^ANTHROPIC_API_KEY=' || echo "no shell-level anthropic var (good — .env will load)"
```

Expected: both keys present in `.env`; no empty shell-level shadow.

If a key is missing or shadowed: stop and ask the user. Do not run the pilot with broken keys (would burn credits on a failed run).

- [ ] **Step 2.2: Verify the recalibrated scenarios load via the CLI's --help path**

```bash
cd nova-agent
NOVA_TIER=production uv run cliff-test --help | head
```

Expected: help output prints; exit code 0. Confirms the binary builds and the recalibrated scenarios.py imports cleanly under production tier resolution.

- [ ] **Step 2.3: Run the pilot**

```bash
cd nova-agent
NOVA_TIER=production uv run cliff-test \
  --scenario all \
  --n 5 \
  --pilot \
  --concurrency 8 \
  --output-dir runs/2026-05-06-pilot-recalibrated 2>&1 | tee runs/2026-05-06-pilot-recalibrated.log
```

Expected wall: ~30 minutes. Expected cost: $5–7 (per spec §5; soft target, no automated abort gate). Run completes with exit code `EXIT_OK` (0); CSV written at `runs/2026-05-06-pilot-recalibrated/pilot_results/cliff_test_results.csv`.

If the run aborts mid-way (exit code `EXIT_SOFT_CAP` or `EXIT_HARD_CAP`): partial CSV may be present; surface to user before adjudication.

- [ ] **Step 2.4: Sanity-check the pilot CSV header + row count**

```bash
cd nova-agent
head -1 runs/2026-05-06-pilot-recalibrated/pilot_results/cliff_test_results.csv
wc -l runs/2026-05-06-pilot-recalibrated/pilot_results/cliff_test_results.csv
```

Expected: header line `scenario_id,trial_index,arm,t_predicts,t_baseline_fails,cost_usd,abort_reason,anxiety_threshold_met,final_move_index,is_right_censored`; row count `31` (1 header + 5 trials × 3 scenarios × 2 arms = 30 data rows).

If row count is short: the run was incomplete — flag to user before adjudication.

---

## Task 3: Adjudicate the four §5 acceptance criteria

**Files:**
- Read: `nova-agent/runs/2026-05-06-pilot-recalibrated/pilot_results/cliff_test_results.csv`

This task is purely analysis — no edits, no commits. The output is a verdict the user adjudicates (PASS → authorise N=20, FAIL → second-round recalibration spec amendment, FLAG → user review).

- [ ] **Step 3.1: Parse the CSV and tabulate per-scenario per-arm metrics**

Use a one-shot Python read (no new tooling — the analysis is small enough to do inline):

```bash
cd nova-agent
uv run python - <<'PY'
import csv
from collections import defaultdict
from statistics import median
from pathlib import Path

CSV = Path("runs/2026-05-06-pilot-recalibrated/pilot_results/cliff_test_results.csv")
WINDOWS = {
    "corner-abandonment-256": (12, 17),
    "snake-collapse-128": (11, 16),
    "512-wall": (12, 17),
}

bot_rows = defaultdict(list)
carla_rows = defaultdict(list)
with CSV.open() as f:
    for r in csv.DictReader(f):
        sid = r["scenario_id"]
        if r["arm"] == "bot":
            bot_rows[sid].append(r)
        else:
            carla_rows[sid].append(r)

print(f"{'scenario':<28} {'in-window':>10} {'cap':>5} {'carla_aborts':>13} {'carla_t_med':>13}")
for sid, lo_hi in WINDOWS.items():
    lo, hi = lo_hi
    bots = bot_rows[sid]
    carlas = carla_rows[sid]
    in_window = sum(1 for r in bots if r["t_baseline_fails"] and lo <= int(r["t_baseline_fails"]) <= hi)
    cap = sum(1 for r in bots if r["is_right_censored"] == "True")
    carla_aborts = sum(1 for r in carlas if r["abort_reason"])
    carla_t_finite = [int(r["t_predicts"]) for r in carlas if r["t_predicts"]]
    carla_t_med = median(carla_t_finite) if carla_t_finite else "N/A"
    print(f"{sid:<28} {in_window:>5}/{len(bots):<3} {cap:>2}/{len(bots):<2} {carla_aborts:>5}/{len(carlas):<5}     {carla_t_med:>10}")
PY
```

Expected: a 4-column-by-3-row table. Save the output to a scratch buffer; it feeds the four-criterion adjudication below.

- [ ] **Step 3.2: Adjudicate criterion 1 — §7.4 calibration**

Per spec §5 acceptance criterion 1: **≥ 3/5 Bot game-overs in `expected_cliff_window` per scenario**.

Read the `in-window` column from Step 3.1 output. For each scenario:
- ≥ 3/5 → PASS
- 1–2/5 → FAIL
- 0/5 → FAIL (re-author the scenario)

- [ ] **Step 3.3: Adjudicate criterion 2 — §2.8 cap discipline (tiered for N=5)**

Per spec §5 acceptance criterion 2 (with red-team operational addendum):

| scenario | acceptance |
|---|---|
| corner-abandonment-256 | 0/5 → PASS; ≥1/5 → FAIL |
| 512-wall | 0/5 → PASS; ≥1/5 → FAIL |
| snake-collapse-128 | 0/5 → PASS; 1/5 → BORDERLINE (flag for user, do not auto-fail); 2+/5 → FAIL |

Read the `cap` column from Step 3.1 output. Apply the tiered rules.

- [ ] **Step 3.4: Adjudicate criterion 3 — Carla deferral**

Per spec §5 acceptance criterion 3:
- corner-abandonment-256: median `t_predicts ∈ [4, 8]` → PASS
- 512-wall: median `t_predicts ∈ [4, 8]` → PASS
- snake-collapse-128: median `t_predicts ≥ 4` → PASS (preserves the working median ≈ 6 within ±2 tolerance)

Read the `carla_t_med` column from Step 3.1 output. Apply per-scenario rules. Note: a median of `0` or `1` here is the fast-reaction failure mode the recalibration was designed to fix — flag it as evidence that the empty-cell + relief-cell adjustments were insufficient.

- [ ] **Step 3.5: Adjudicate criterion 4 — operational (Carla aborts)**

Per spec §5 acceptance criterion 4 (with red-team operational addendum): **0 Carla aborts across the 15 Carla trials**.

Read the `carla_aborts` column from Step 3.1 output. Sum across scenarios. 0 → PASS; 1+ → FAIL (investigate; either the Sonnet ToT path has a stability issue, or there's a bus / memory / api-error mid-run that masks scenario-level signal).

- [ ] **Step 3.6: Compose the verdict report**

Produce a short report for the user with:

1. The Step 3.1 table (raw metrics).
2. Per-criterion verdict (PASS / FAIL / BORDERLINE).
3. Overall outcome:
   - **All four PASS (snake cap may be 0/5 or 1/5-flagged):** authorise the real N=20 run. Next step: write the `analyze_results.py` spec, then schedule the N=20 run.
   - **Any FAIL:** identify which criterion + which scenario; recommend second-round recalibration as a spec amendment to `2026-05-06-scenarios-recalibration-design.md` (Amendment 1) per the spec's "If any criterion fails ... amended in place" rule. Surface the failing scenario's pilot data so the next round has data to design against.
   - **Snake BORDERLINE (1/5 cap):** present the data, recommend user review per the addendum ("flag for review, do not auto-fail").
4. Cost actuals (sum of `cost_usd` across all rows) vs the $5–7 budget — informational; even if over $7, no automatic action (operational-only budget).

Send the report to the user. Do not auto-proceed to N=20 or to a second-round amendment without explicit user authorisation.

---

## After Task 3

- **PASS path:** Per spec §6, the next deferred work is the `analyze_results.py` spec. Invoke `superpowers:brainstorming` for that spec when the user authorises N=20 prep.
- **FAIL path:** Amend `2026-05-06-scenarios-recalibration-design.md` in place with Amendment 1 (per the spec's own §5 "amended in place" rule); the amendment specifies the second-round matrix for the failing scenario(s). The current plan file is reusable — restart at Task 1 with the amended grids.
- **BORDERLINE path:** Per addendum, the user reviews and chooses PASS-with-flag (proceed to N=20 with snake's borderline status documented) or FAIL (second-round recalibration on snake only).

This plan is single-session-suitable (Task 1 ~10 min, Task 2 ~30 min wall, Task 3 ~5 min). One human-supervised loop.
