import asyncio
import json
import pytest
import websockets
from nova_agent.bus.websocket import EventBus


@pytest.mark.asyncio
async def test_event_bus_publishes_to_subscriber():
    bus = EventBus(host="127.0.0.1", port=18765)
    await bus.start()
    received = []
    async with websockets.connect("ws://127.0.0.1:18765") as ws:
        await asyncio.sleep(0.1)
        await bus.publish("test_event", {"x": 1})
        msg = await asyncio.wait_for(ws.recv(), timeout=2.0)
        received.append(json.loads(msg))
    await bus.stop()
    assert received == [{"event": "test_event", "data": {"x": 1}}]


@pytest.mark.asyncio
async def test_publish_drops_frame_on_slow_client(monkeypatch):
    """R4 — a slow client cannot stall the agent loop.

    Simulate a client whose `ws.send` blocks longer than SEND_TIMEOUT_S.
    `bus.publish` must return promptly (within ~2× timeout) without raising.
    """
    bus = EventBus(host="127.0.0.1", port=18766)
    bus.SEND_TIMEOUT_S = 0.05

    class SlowSocket:
        async def send(self, _payload: str) -> None:
            await asyncio.sleep(1.0)  # simulate buffer-full backpressure

    EventBus._drop_counter = 0
    bus._clients.add(SlowSocket())  # type: ignore[arg-type]

    start = asyncio.get_running_loop().time()
    await bus.publish("evt", {"k": 1})
    elapsed = asyncio.get_running_loop().time() - start
    assert elapsed < 0.2, f"publish stalled for {elapsed:.3f}s on slow client"
    assert EventBus._drop_counter >= 1
