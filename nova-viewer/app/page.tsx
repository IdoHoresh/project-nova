"use client";

import { useEffect, useState } from "react";

type AgentEvent = { event: string; data: unknown };

export default function Home() {
  const [events, setEvents] = useState<AgentEvent[]>([]);

  useEffect(() => {
    const url = `ws://${process.env.NEXT_PUBLIC_WS_HOST ?? "127.0.0.1"}:${
      process.env.NEXT_PUBLIC_WS_PORT ?? "8765"
    }`;
    const ws = new WebSocket(url);
    ws.onmessage = (e) => {
      try {
        const msg = JSON.parse(e.data) as AgentEvent;
        setEvents((prev) => [...prev.slice(-49), msg]);
      } catch {}
    };
    return () => ws.close();
  }, []);

  return (
    <main className="min-h-screen bg-[#1a1614] text-zinc-100 p-8 font-mono text-sm">
      <h1 className="text-2xl mb-4">Project Nova — brain panel (placeholder)</h1>
      <div className="grid grid-cols-2 gap-8">
        <section className="bg-zinc-900/50 rounded p-4">
          <h2 className="text-lg mb-2 text-zinc-400">Live game (placeholder)</h2>
          <div className="aspect-[9/16] bg-black rounded" />
        </section>
        <section className="bg-zinc-900/50 rounded p-4 overflow-y-auto max-h-[80vh]">
          <h2 className="text-lg mb-2 text-zinc-400">Events ({events.length})</h2>
          <ul className="space-y-1">
            {events.map((e, i) => (
              <li key={i} className="text-xs">
                <span className="text-cyan-400">{e.event}</span> —{" "}
                <span className="text-zinc-400">{JSON.stringify(e.data)}</span>
              </li>
            ))}
          </ul>
        </section>
      </div>
    </main>
  );
}
