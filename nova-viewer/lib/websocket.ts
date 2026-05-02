"use client";

import { useEffect, useRef, useState } from "react";
import type { AgentEvent } from "./types";
import { parseAgentEvent } from "./eventGuards";

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
  const seenInvalidEventsRef = useRef<Set<string>>(new Set());

  useEffect(() => {
    const url = `ws://${process.env.NEXT_PUBLIC_WS_HOST ?? "127.0.0.1"}:${
      process.env.NEXT_PUBLIC_WS_PORT ?? "8765"
    }`;
    const ws = new WebSocket(url);
    ws.onopen = () => setConnected(true);
    ws.onclose = () => setConnected(false);
    ws.onmessage = (e) => {
      let raw: unknown;
      try {
        raw = JSON.parse(e.data);
      } catch {
        // Malformed JSON — drop without further parsing.
        return;
      }
      const parsed = parseAgentEvent(raw);
      if (parsed === null) {
        // Frame parsed as JSON but failed schema validation. Log once per
        // session per event name to avoid flooding the console on bad
        // streams. The agent should never emit malformed events; if this
        // fires the agent code or this validator is out of sync.
        const evName =
          raw && typeof raw === "object" && "event" in raw
            ? String((raw as { event: unknown }).event)
            : "<no event>";
        const seen = seenInvalidEventsRef.current;
        if (!seen.has(evName)) {
          seen.add(evName);
          console.warn(
            `[useNovaSocket] dropped invalid frame for event="${evName}"`,
            raw,
          );
        }
        return;
      }
      const msg: StampedAgentEvent = { ...parsed, ts: new Date().toISOString() };
      setEvents((prev) => [...prev.slice(-99), msg]);
    };
    return () => ws.close();
  }, []);

  return { events, connected };
}
