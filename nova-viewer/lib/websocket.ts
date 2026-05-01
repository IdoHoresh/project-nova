"use client";

import { useEffect, useState } from "react";
import type { AgentEvent } from "./types";

export function useNovaSocket() {
  const [events, setEvents] = useState<AgentEvent[]>([]);
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
        const msg = JSON.parse(e.data) as AgentEvent;
        setEvents((prev) => [...prev.slice(-99), msg]);
      } catch {
        // ignore malformed frames
      }
    };
    return () => ws.close();
  }, []);

  return { events, connected };
}
