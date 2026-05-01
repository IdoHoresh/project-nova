"use client";

import { useMemo } from "react";

import { MemoryFeed } from "./components/MemoryFeed";
import { useNovaSocket } from "@/lib/websocket";
import type { RetrievedMemoryDTO } from "@/lib/types";

export default function Home() {
  const { events, connected } = useNovaSocket();

  const memories = useMemo<RetrievedMemoryDTO[]>(() => {
    for (let i = events.length - 1; i >= 0; i--) {
      const e = events[i];
      if (e.event === "memory_retrieved") {
        const data = e.data as { items?: RetrievedMemoryDTO[] };
        if (Array.isArray(data.items)) return data.items;
      }
    }
    return [];
  }, [events]);

  return (
    <main className="min-h-screen bg-[#1a1614] text-zinc-100 p-8 font-mono text-sm">
      <header className="flex justify-between items-baseline mb-4">
        <h1 className="text-2xl">Project Nova — brain panel</h1>
        <span
          className={`text-xs ${
            connected ? "text-emerald-400" : "text-zinc-500"
          }`}
        >
          {connected ? "● live" : "○ disconnected"}
        </span>
      </header>

      <div className="grid grid-cols-3 gap-8">
        <section className="bg-zinc-900/50 rounded p-4">
          <h2 className="text-lg mb-2 text-zinc-400">Live game (placeholder)</h2>
          <div className="aspect-[9/16] bg-black rounded" />
        </section>

        <section className="bg-zinc-900/50 rounded p-4 overflow-y-auto max-h-[80vh]">
          <MemoryFeed items={memories} />
        </section>

        <section className="bg-zinc-900/50 rounded p-4 overflow-y-auto max-h-[80vh]">
          <h2 className="text-lg mb-2 text-zinc-400">Events ({events.length})</h2>
          <ul className="space-y-1">
            {events.map((e, i) => (
              <li key={i} className="text-xs">
                <span className="text-cyan-400">{e.event}</span>
                <span className="text-zinc-500"> — </span>
                <span className="text-zinc-400">{JSON.stringify(e.data)}</span>
              </li>
            ))}
          </ul>
        </section>
      </div>
    </main>
  );
}
