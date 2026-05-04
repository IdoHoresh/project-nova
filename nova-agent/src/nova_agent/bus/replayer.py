"""Replay a recorded AgentEvent stream as a WebSocket source.

Pairs with `nova_agent.bus.recorder` to enable record-once / replay-many
UI development. Reads a JSONL file produced by `RecordingEventBus`,
broadcasts each event to connected clients with original inter-event
timing (optionally compressed by a `time_warp` factor).

Usage as a script:

    uv run python -m nova_agent.bus.replayer --file game.jsonl --port 8765

Usage as a library:

    server = ReplayServer(path="game.jsonl", host="127.0.0.1", port=8765)
    await server.run()  # blocks until file is exhausted

Behavior:

- Waits for at least one client to connect before starting playback. This
  matches the typical UI-dev flow: start the replayer, open the viewer in
  a browser, see the recorded session play back.
- Honors the recorded `t` deltas to preserve animation timing — pulses,
  fades, mode transitions all look natural.
- `time_warp` < 1.0 plays back faster than real-time (e.g. 0.1 = 10x
  speed); > 1.0 plays back slower; default 1.0 = real-time.
- After the recording is exhausted the server logs `replay.file_exhausted`
  and remains running until the process is killed; reconnecting clients
  receive nothing until the replayer is restarted. (Loop-on-reconnect
  is not implemented — scope creep for a UI-dev tool.)
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path
from typing import Any

import structlog
import websockets
from websockets.asyncio.server import Server, ServerConnection, serve as ws_serve

log = structlog.get_logger()


class ReplayServer:
    """WebSocket server that broadcasts a pre-recorded JSONL event stream."""

    def __init__(
        self,
        *,
        path: str | Path,
        host: str = "127.0.0.1",
        port: int = 8765,
        time_warp: float = 1.0,
    ) -> None:
        self._path = Path(path)
        self._host = host
        self._port = port
        if time_warp <= 0:
            raise ValueError(f"time_warp must be > 0, got {time_warp!r}")
        self._time_warp = time_warp
        self._clients: set[ServerConnection] = set()
        self._server: Server | None = None
        self._first_client_connected: asyncio.Event = asyncio.Event()

    async def _handler(self, ws: ServerConnection) -> None:
        self._clients.add(ws)
        log.info("replay.client_connected", count=len(self._clients))
        self._first_client_connected.set()
        try:
            async for _ in ws:
                pass  # ignore inbound; broadcast-only
        finally:
            self._clients.discard(ws)
            log.info("replay.client_disconnected", count=len(self._clients))

    async def run(self) -> None:
        """Start the server, wait for first client, then play back the file."""
        self._server = await ws_serve(self._handler, self._host, self._port)
        log.info(
            "replay.started",
            host=self._host,
            port=self._port,
            path=str(self._path),
            time_warp=self._time_warp,
        )
        try:
            await self._first_client_connected.wait()
            await self._playback()
        finally:
            self._server.close()
            await self._server.wait_closed()
            log.info("replay.stopped")

    async def _playback(self) -> None:
        loop = asyncio.get_running_loop()
        playback_started_at = loop.time()
        # Read the whole file off-thread so JSON parsing doesn't block the
        # event loop; recordings are small (~50 events for a 50-move game)
        # so single-shot read is fine. Switch to chunked streaming if a
        # multi-game recording ever shows up.
        records = await asyncio.to_thread(_load_records, self._path)
        for record in records:
            target_t = float(record["t"]) * self._time_warp
            now = loop.time() - playback_started_at
            wait_for = target_t - now
            if wait_for > 0:
                await asyncio.sleep(wait_for)
            await self._broadcast(record["event"], record["data"])
        log.info("replay.file_exhausted")

    async def _broadcast(self, event: str, data: Any) -> None:
        if not self._clients:
            return
        payload = json.dumps({"event": event, "data": data}, default=str)
        await asyncio.gather(
            *(self._safe_send(ws, payload) for ws in list(self._clients)),
            return_exceptions=True,
        )

    @staticmethod
    async def _safe_send(ws: ServerConnection, payload: str) -> None:
        try:
            await ws.send(payload)
        except websockets.exceptions.ConnectionClosed:
            # Client disconnected mid-broadcast; nothing to do — the
            # connection-close path in _handler will clean up _clients.
            pass
        except OSError as e:
            log.warning("replay.send_failed", error=str(e))


def _load_records(path: Path) -> list[dict[str, Any]]:
    """Read a JSONL file into a list of records, skipping blank lines.

    Runs on a worker thread (via asyncio.to_thread) so the event loop
    doesn't block on file I/O or JSON parsing.
    """
    records: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as fh:
        for raw_line in fh:
            line = raw_line.strip()
            if not line:
                continue
            records.append(json.loads(line))
    return records


def _parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="nova_agent.bus.replayer",
        description="Replay a recorded AgentEvent stream over WebSocket for UI dev.",
    )
    p.add_argument("--file", required=True, help="Path to JSONL recording")
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=8765)
    p.add_argument(
        "--time-warp",
        type=float,
        default=1.0,
        help="Multiply inter-event delays by this factor. <1 = faster, >1 = slower.",
    )
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = _parse_args(argv if argv is not None else sys.argv[1:])
    server = ReplayServer(
        path=args.file,
        host=args.host,
        port=args.port,
        time_warp=args.time_warp,
    )
    asyncio.run(server.run())


if __name__ == "__main__":
    main()
