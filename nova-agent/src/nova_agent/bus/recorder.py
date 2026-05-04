"""Recording subclass of EventBus that appends every published event to a
newline-delimited JSON file alongside the live WebSocket broadcast.

Pairs with `nova_agent.bus.replayer` to enable the record-once / replay-many
workflow for UI development without paying the LLM cost of fresh games.

Each line is a JSON object with shape:

    {"t": <monotonic seconds since recording started>, "event": <name>, "data": <payload>}

The `t` field is a monotonic-clock delta, not a wall clock — it preserves
inter-event spacing during replay without leaking developer-system clock
information into the recording.

Bus protocol note: this class mirrors the existing `EventBus.publish(event:
str, data: Any)` signature intentionally. The typed-bus protocol effort
tracked at `nova_agent/bus/protocol.py` (TBD ADR per `LESSONS.md`) will
tighten both signatures together; recorder must NOT extend the untyped
surface independently.

Usage:

    bus = RecordingEventBus(host="127.0.0.1", port=8765, path="game.jsonl")
    await bus.start()
    # ... agent runs, events are broadcast AND written to game.jsonl
    await bus.stop()  # closes the file handle cleanly
"""

from __future__ import annotations

import asyncio
import json
import time
from pathlib import Path
from typing import Any, TextIO

import structlog

from nova_agent.bus.websocket import EventBus

log = structlog.get_logger()


class RecordingEventBus(EventBus):
    """EventBus that ALSO appends each published event to a JSONL file.

    The recording file is opened lazily on first publish so that creating
    the bus does not touch the filesystem until events actually flow.

    Disk writes are offloaded to a worker thread via asyncio.to_thread so
    the agent's event loop never blocks on filesystem latency — broadcast
    is load-bearing for the agent's decision cadence (per the R4 timeout
    in EventBus._safe_send).
    """

    def __init__(
        self,
        *,
        host: str = "127.0.0.1",
        port: int = 8765,
        path: str | Path,
    ) -> None:
        super().__init__(host=host, port=port)
        self._record_path = Path(path)
        self._fh: TextIO | None = None
        self._recording_started_at: float = 0.0
        self._recording_active: bool = False

    async def publish(self, event: str, data: Any) -> None:
        # Disk write before broadcast so a recorder developer notices missing
        # frames at recording time, not at replay time. Still, swallow disk
        # errors with a structured log line — the recording is best-effort,
        # the live broadcast is load-bearing.
        try:
            await asyncio.to_thread(self._write_line_sync, event, data)
        except OSError as e:
            log.warning("bus.record_write_failed", path=str(self._record_path), error=str(e))
        await super().publish(event, data)

    async def stop(self) -> None:
        await super().stop()
        if self._fh is not None:
            self._fh.close()
            self._fh = None
            self._recording_active = False
            log.info("bus.record_stopped", path=str(self._record_path))

    def _write_line_sync(self, event: str, data: Any) -> None:
        """Synchronous JSONL append. Runs on a worker thread.

        Raises:
            OSError: any filesystem error (caller logs and continues)
            TypeError: payload contains a type the JSON encoder cannot
                serialize. Surfaces schema drift instead of hiding it.
        """
        if self._fh is None:
            self._record_path.parent.mkdir(parents=True, exist_ok=True)
            self._fh = self._record_path.open("a", encoding="utf-8")
            self._recording_started_at = time.monotonic()
            self._recording_active = True
            log.info("bus.record_started", path=str(self._record_path))
        delta = time.monotonic() - self._recording_started_at
        # No `default=str` — bus payloads should already be JSON-native (per
        # pydantic-validated boundary). A TypeError here flags real schema
        # drift between the producer and the recording format.
        line = json.dumps({"t": delta, "event": event, "data": data})
        self._fh.write(line)
        self._fh.write("\n")
        self._fh.flush()
