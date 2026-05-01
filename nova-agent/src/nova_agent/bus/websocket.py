"""Local WebSocket broadcaster.

Plan-vs-reality fix: plan imports `WebSocketServerProtocol` from
`websockets.server`, which is deprecated in websockets >= 14. We use
the modern `websockets.asyncio.server.ServerConnection` interface
(stable in websockets 16, our installed version).
"""

import asyncio
import json
from typing import Any

import structlog
import websockets
from websockets.asyncio.server import ServerConnection, serve as ws_serve
from websockets.asyncio.server import Server

log = structlog.get_logger()


class EventBus:
    """Local WebSocket broadcaster. Connections subscribe; agent publishes."""

    SEND_TIMEOUT_S: float = 0.1  # R4 — protect agent loop from UI lag
    _drop_counter: int = 0

    def __init__(self, *, host: str = "127.0.0.1", port: int = 8765):
        self.host = host
        self.port = port
        self._clients: set[ServerConnection] = set()
        self._server: Server | None = None

    async def _handler(self, ws: ServerConnection) -> None:
        self._clients.add(ws)
        log.info("bus.client_connected", count=len(self._clients))
        try:
            async for _ in ws:
                pass  # ignore inbound; broadcast-only
        finally:
            self._clients.discard(ws)
            log.info("bus.client_disconnected", count=len(self._clients))

    async def start(self) -> None:
        self._server = await ws_serve(self._handler, self.host, self.port)
        log.info("bus.started", host=self.host, port=self.port)

    async def stop(self) -> None:
        if self._server:
            self._server.close()
            await self._server.wait_closed()

    async def publish(self, event: str, data: Any) -> None:
        payload = json.dumps({"event": event, "data": data}, default=str)
        if not self._clients:
            return
        await asyncio.gather(
            *(self._safe_send(ws, payload) for ws in list(self._clients)),
            return_exceptions=True,
        )

    async def _safe_send(self, ws: ServerConnection, payload: str) -> None:
        """R4 — per-send timeout. A backgrounded Chrome tab can keep the
        WebSocket open but stop ACKing packets. Without a timeout `ws.send`
        blocks until the OS-level send buffer drains, stalling the decision
        loop on UI lag. Drop the frame instead — the brain panel can miss
        a frame; the agent cannot stall.
        """
        try:
            await asyncio.wait_for(ws.send(payload), timeout=self.SEND_TIMEOUT_S)
        except asyncio.TimeoutError:
            type(self)._drop_counter += 1
            log.warning("bus.send_timeout_dropped", drops=type(self)._drop_counter)
        except websockets.exceptions.ConnectionClosed:
            pass  # client disconnected mid-send; cleanup happens in _handler
