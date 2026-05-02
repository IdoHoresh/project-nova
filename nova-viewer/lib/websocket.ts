"use client";

import { useEffect, useState } from "react";
import type { AgentEvent } from "./types";

/**
 * AgentEvent stamped with a wall-clock arrival time.
 *
 * The bus protocol does not carry timestamps (the backend emits events as
 * they happen and assumes consumers can stamp on receipt). Without a per-
 * event timestamp the viewer's stream entries all read the SAME time
 * (whatever moment deriveStream last re-ran), which the user explicitly
 * flagged as wrong. This wraps each parsed message so downstream code can
 * read `e.ts` and render the actual moment the event arrived.
 */
export type StampedAgentEvent = AgentEvent & { ts: string };

export function useNovaSocket() {
  const [events, setEvents] = useState<StampedAgentEvent[]>([]);
  const [connected, setConnected] = useState(false);

  useEffect(() => {
    const url = `ws://${process.env.NEXT_PUBLIC_WS_HOST ?? "127.0.0.1"}:${
      process.env.NEXT_PUBLIC_WS_PORT ?? "8765"
    }`;
    const ws = new WebSocket(url);
    ws.onopen = () => setConnected(true);
    ws.onclose = () => setConnected(false);
    ws.onmessage = (e) => {
      try {
        const parsed = JSON.parse(e.data) as AgentEvent;
        const msg: StampedAgentEvent = { ...parsed, ts: new Date().toISOString() };
        setEvents((prev) => [...prev.slice(-99), msg]);
      } catch {
        // ignore malformed frames
      }
    };
    return () => ws.close();
  }, []);

  return { events, connected };
}
