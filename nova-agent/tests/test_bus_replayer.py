"""Tests for `ReplayServer` — serves a pre-recorded JSONL stream over WebSocket."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

import pytest
import websockets

from nova_agent.bus.replayer import ReplayServer


def _write_recording(path: Path, records: list[dict]) -> None:
    with path.open("w", encoding="utf-8") as fh:
        for r in records:
            fh.write(json.dumps(r))
            fh.write("\n")


@pytest.mark.asyncio
async def test_replayer_serves_recorded_stream_in_order(tmp_path: Path) -> None:
    """Connected clients receive every recorded event, in the recorded order."""
    rec_path = tmp_path / "session.jsonl"
    _write_recording(
        rec_path,
        [
            {"t": 0.0, "event": "perception", "data": {"score": 0}},
            {"t": 0.0, "event": "decision", "data": {"move": "up"}},
            {"t": 0.0, "event": "perception", "data": {"score": 4}},
        ],
    )
    server = ReplayServer(path=rec_path, host="127.0.0.1", port=18901, time_warp=1.0)

    async def consume() -> list[dict]:
        async with websockets.connect("ws://127.0.0.1:18901") as ws:
            collected: list[dict] = []
            for _ in range(3):
                msg = await asyncio.wait_for(ws.recv(), timeout=2.0)
                collected.append(json.loads(msg))
            return collected

    server_task = asyncio.create_task(server.run())
    try:
        # Give the server a moment to start listening before the client connects.
        await asyncio.sleep(0.1)
        received = await consume()
    finally:
        server_task.cancel()
        try:
            await server_task
        except (asyncio.CancelledError, Exception):
            pass

    events = [r["event"] for r in received]
    scores = [r["data"].get("score") for r in received if r["event"] == "perception"]
    assert events == ["perception", "decision", "perception"]
    assert scores == [0, 4]


@pytest.mark.asyncio
async def test_replayer_respects_time_warp(tmp_path: Path) -> None:
    """time_warp=0.1 plays back ~10x faster than the recorded deltas."""
    rec_path = tmp_path / "session.jsonl"
    _write_recording(
        rec_path,
        [
            {"t": 0.0, "event": "a", "data": {}},
            {"t": 0.5, "event": "b", "data": {}},
            {"t": 1.0, "event": "c", "data": {}},
        ],
    )
    server = ReplayServer(path=rec_path, host="127.0.0.1", port=18902, time_warp=0.1)
    server_task = asyncio.create_task(server.run())
    try:
        await asyncio.sleep(0.1)
        async with websockets.connect("ws://127.0.0.1:18902") as ws:
            loop = asyncio.get_running_loop()
            start = loop.time()
            for _ in range(3):
                await asyncio.wait_for(ws.recv(), timeout=2.0)
            elapsed = loop.time() - start
        # Recorded span = 1.0s. With time_warp=0.1, expect ~0.1s.
        # Generous upper bound for CI noise.
        assert elapsed < 0.4, f"replay took {elapsed:.3f}s, expected ~0.1s"
    finally:
        server_task.cancel()
        try:
            await server_task
        except (asyncio.CancelledError, Exception):
            pass


@pytest.mark.asyncio
async def test_replayer_waits_for_first_client(tmp_path: Path) -> None:
    """Playback does not start until a client is connected — otherwise the
    file would be exhausted before the viewer can subscribe."""
    rec_path = tmp_path / "session.jsonl"
    _write_recording(
        rec_path,
        [{"t": 0.0, "event": "first", "data": {}}],
    )
    server = ReplayServer(path=rec_path, host="127.0.0.1", port=18903, time_warp=1.0)
    server_task = asyncio.create_task(server.run())
    try:
        # Wait long enough that, if the server were broadcasting blindly, it
        # would have finished. Then connect — we should still receive the event.
        await asyncio.sleep(0.3)
        async with websockets.connect("ws://127.0.0.1:18903") as ws:
            msg = await asyncio.wait_for(ws.recv(), timeout=2.0)
        assert json.loads(msg)["event"] == "first"
    finally:
        server_task.cancel()
        try:
            await server_task
        except (asyncio.CancelledError, Exception):
            pass


def test_replayer_rejects_non_positive_time_warp(tmp_path: Path) -> None:
    """time_warp must be > 0 — zero or negative makes no sense and would
    either divide-by-zero or replay backwards."""
    rec_path = tmp_path / "session.jsonl"
    rec_path.write_text("")
    with pytest.raises(ValueError, match="time_warp"):
        ReplayServer(path=rec_path, host="127.0.0.1", port=18904, time_warp=0)
    with pytest.raises(ValueError, match="time_warp"):
        ReplayServer(path=rec_path, host="127.0.0.1", port=18904, time_warp=-1.0)
