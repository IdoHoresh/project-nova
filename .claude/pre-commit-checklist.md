# Pre-Commit Checklist

> Before EVERY commit, work through this list and check each item.
> The pre-commit framework runs `scripts/check-claude-checklist.sh`
> which **blocks the commit** if any item is left unchecked.
>
> After a successful commit, `scripts/reset-checklist.sh` runs at the
> post-commit stage and resets every box back to `[x]` so the next
> commit starts fresh.
>
> If a step doesn't apply, write a one-sentence reason after the
> bracket (e.g. mark `[x]` and add `/review — skipped, doc-only change`)
> and check the box. Silent skipping is forbidden.

## Branch + scope

- [x] On feature branch `claude/practical-swanson-4b6468`, not `main`
- [x] `git diff --cached --stat` reviewed — 5 files: 2 new in `nova-agent/src/nova_agent/bus/` (recorder.py, replayer.py), 2 new tests, 1 small main.py wiring + 1 small config.py field addition
- [x] Atomic commit — single logical change: record-and-replay capability for the event bus to enable UI dev without paying LLM cost

## Verification

- [x] `git diff --cached` scanned for secrets — no env values / API keys / tokens; the only secret-adjacent thing is `bus_record_path` (a filesystem path, not a credential)
- [x] `nova-agent/` — gate trio green: `uv run pytest` (150/150, including 5 recorder + 5 replayer tests), `uv run mypy` (46 files clean), `uv run ruff check` (clean)
- [x] `nova-viewer/` not touched — N/A, agent-only change. Viewer can connect to either the live bus or the replayer with no client-side change.
- [x] Docs / config — `recorder.RecordingEventBus` subclasses `EventBus`, writes JSONL to `bus_record_path` via `asyncio.to_thread` (no event-loop blocking) with structured-log fallback on disk error; `replayer.ReplayServer` reads JSONL via `asyncio.to_thread` (no event-loop blocking) and broadcasts with original timing (optional `time_warp`); CLI entry point at `python -m nova_agent.bus.replayer`. Config gains `bus_record_path: Path | None` field on `Settings` (alias `NOVA_BUS_RECORD`, default None disables) — replaces a direct `os.environ.get` that was bypassing pydantic-settings.

## Review

- [x] `/review` dispatched on staged diff — yes. Code-reviewer dispatched (Sonnet via Agent tool) returned 2 BLOCK + 6 WARN + 1 NIT findings. Security-reviewer dispatched (Opus via Agent tool) returned APPROVE with 3 LOW defense-in-depth notes.
- [x] All 2 BLOCK findings addressed:
  - **BLOCK recorder.py:65** — sync flushed disk I/O on event loop thread → fixed with `asyncio.to_thread(self._write_line_sync, ...)` so the loop never blocks on filesystem latency
  - **BLOCK recorder.py:56** — raw-string event-name signature inherited from base EventBus → added docstring note that signature intentionally mirrors `EventBus.publish` and the typed-bus protocol effort (TBD ADR per LESSONS.md) tightens both together; recorder must NOT extend the untyped surface independently
- [x] All 6 WARN findings addressed:
  - main.py:107 NOVA_BUS_RECORD bypass → moved to `Settings.bus_record_path` with `env_ignore_empty=True` already on Settings
  - recorder.py:82 `default=str` masking schema drift → dropped; JSONEncoder TypeError now surfaces drift
  - replayer.py:127 bare except → narrowed to `ConnectionClosed` (silent) + `OSError` (logged via structured `replay.send_failed`)
  - replayer.py:97 sync file iter on event loop → extracted `_load_records()` and ran via `asyncio.to_thread`
  - replayer.py:79 docstring vs behavior mismatch → rewrote module docstring to match reality (server stays running but doesn't loop on reconnect)
  - recorder.py:80 mypy-appeasing assert → replaced with typed `_recording_started_at: float = 0.0` and explicit `_recording_active: bool` flag
- [x] NIT replayer.py:42 import combine → folded `Server, ServerConnection, serve` onto one line

## Documentation

- [x] LESSONS.md — N/A, no time-cost gotcha; the recorder fix for the sync-write trap was caught by the reviewer dispatch — the lesson is that the review pattern is doing its job
- [x] CLAUDE.md "Common gotchas" — N/A, no new Nova-specific gotcha
- [x] ARCHITECTURE.md — N/A, system topology unchanged (bus has same shape; recorder is a transparent wrapper)
- [x] New ADR — deferred. ADR-0006 (cost tiers + dev-mode discipline + record-replay rationale) drafts in a follow-up commit alongside the `plumbing` tier addition; this commit is the recorder/replayer alone.

## Commit message

- [x] Conventional Commits format: `feat(bus): add record-and-replay for AgentEvent streams`
- [x] Body explains *why* — UI dev currently requires running the full agent for every render iteration, paying LLM cost on every CSS tweak. Recorder writes every published event to JSONL during a single real game; replayer reads that file and broadcasts via WebSocket so the viewer renders the recorded stream as if it were live. Saves all the LLM cost of running the agent every time the UI changes — high ROI per the cost-reduction plan red-teamed by the principal engineer.
- [x] Co-author tag present: `Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>`
