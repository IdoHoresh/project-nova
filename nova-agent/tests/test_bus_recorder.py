"""Tests for `RecordingEventBus` — broadcasts AND writes JSONL to disk."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

import pytest
import websockets

from nova_agent.bus.recorder import RecordingEventBus


@pytest.mark.asyncio
async def test_recorder_writes_jsonl_lines(tmp_path: Path) -> None:
    """Each publish call writes one valid JSONL line with t/event/data fields."""
    record_path = tmp_path / "session.jsonl"
    bus = RecordingEventBus(host="127.0.0.1", port=18801, path=record_path)
    await bus.start()
    try:
        await bus.publish("perception", {"score": 4})
        await bus.publish("decision", {"move": "up"})
    finally:
        await bus.stop()

    lines = record_path.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 2
    rec0 = json.loads(lines[0])
    rec1 = json.loads(lines[1])
    assert rec0["event"] == "perception"
    assert rec0["data"] == {"score": 4}
    assert rec1["event"] == "decision"
    assert rec1["data"] == {"move": "up"}
    assert isinstance(rec0["t"], (int, float))
    assert rec0["t"] >= 0
    assert rec1["t"] >= rec0["t"]


@pytest.mark.asyncio
async def test_recorder_preserves_timing_deltas(tmp_path: Path) -> None:
    """Inter-event `t` deltas must be monotonically non-decreasing AND
    reflect real elapsed time (loose tolerance)."""
    record_path = tmp_path / "session.jsonl"
    bus = RecordingEventBus(host="127.0.0.1", port=18802, path=record_path)
    await bus.start()
    try:
        await bus.publish("a", {})
        await asyncio.sleep(0.05)
        await bus.publish("b", {})
        await asyncio.sleep(0.05)
        await bus.publish("c", {})
    finally:
        await bus.stop()

    deltas = [json.loads(line)["t"] for line in record_path.read_text().strip().splitlines()]
    assert deltas[0] < deltas[1] < deltas[2]
    # Allow generous tolerance — CI is slow, sleeps are not exact.
    assert deltas[1] - deltas[0] >= 0.04
    assert deltas[2] - deltas[1] >= 0.04


@pytest.mark.asyncio
async def test_recorder_still_broadcasts_to_websocket(tmp_path: Path) -> None:
    """Recording must NOT silently swallow the live broadcast — viewers
    connected during a recorded session must still receive frames."""
    record_path = tmp_path / "session.jsonl"
    bus = RecordingEventBus(host="127.0.0.1", port=18803, path=record_path)
    await bus.start()
    try:
        async with websockets.connect("ws://127.0.0.1:18803") as ws:
            await asyncio.sleep(0.05)
            await bus.publish("hello", {"x": 1})
            msg = await asyncio.wait_for(ws.recv(), timeout=2.0)
        assert json.loads(msg) == {"event": "hello", "data": {"x": 1}}
    finally:
        await bus.stop()


@pytest.mark.asyncio
async def test_recorder_creates_parent_directory(tmp_path: Path) -> None:
    """If the recording path's parent dir doesn't exist, recorder creates it."""
    record_path = tmp_path / "nested" / "subdir" / "session.jsonl"
    assert not record_path.parent.exists()
    bus = RecordingEventBus(host="127.0.0.1", port=18804, path=record_path)
    await bus.start()
    try:
        await bus.publish("evt", {"k": 1})
    finally:
        await bus.stop()
    assert record_path.exists()
    assert record_path.parent.is_dir()


@pytest.mark.asyncio
async def test_recorder_disk_failure_does_not_break_broadcast(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """If the JSONL write fails (permission error, disk full, etc.), the live
    broadcast must still succeed — recording is best-effort, broadcast is
    load-bearing for the agent loop."""
    record_path = tmp_path / "session.jsonl"
    bus = RecordingEventBus(host="127.0.0.1", port=18805, path=record_path)
    await bus.start()

    # Replace the writer with a function that always raises OSError.
    def boom(*_args: object, **_kwargs: object) -> None:
        raise OSError("simulated disk full")

    monkeypatch.setattr(bus, "_write_line_sync", boom)

    try:
        async with websockets.connect("ws://127.0.0.1:18805") as ws:
            await asyncio.sleep(0.05)
            await bus.publish("survives_disk_failure", {"y": 2})
            msg = await asyncio.wait_for(ws.recv(), timeout=2.0)
        assert json.loads(msg)["event"] == "survives_disk_failure"
    finally:
        await bus.stop()


def test_recorder_init_does_not_touch_disk(tmp_path: Path) -> None:
    """Lazy file open: constructing the bus alone should NOT create the file."""
    record_path = tmp_path / "session.jsonl"
    RecordingEventBus(host="127.0.0.1", port=18806, path=record_path)
    assert not record_path.exists()
