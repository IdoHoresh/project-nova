"use client";

import { useMemo } from "react";

import { AffectLabel } from "./components/AffectLabel";
import { DopamineBar } from "./components/DopamineBar";
import { MemoryFeed } from "./components/MemoryFeed";
import { MoodGauge } from "./components/MoodGauge";
import { useNovaSocket } from "@/lib/websocket";
import type {
  AffectVectorDTO,
  RetrievedMemoryDTO,
} from "@/lib/types";

const NEUTRAL_AFFECT: AffectVectorDTO = {
  valence: 0,
  arousal: 0.2,
  dopamine: 0,
  frustration: 0,
  anxiety: 0,
  confidence: 0.5,
};

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

  const affect = useMemo<AffectVectorDTO>(() => {
    for (let i = events.length - 1; i >= 0; i--) {
      const e = events[i];
      if (e.event === "affect") {
        const d = e.data as AffectVectorDTO;
        return d;
      }
    }
    return NEUTRAL_AFFECT;
  }, [events]);

  const affectText = useMemo<string>(() => {
    for (let i = events.length - 1; i >= 0; i--) {
      const e = events[i];
      if (e.event === "decision") {
        const d = e.data as { affect_text?: string };
        if (d.affect_text) return d.affect_text;
      }
    }
    return "";
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

        <section className="bg-zinc-900/50 rounded p-4 space-y-6">
          <AffectLabel text={affectText} />
          <div className="flex items-start gap-8">
            <MoodGauge valence={affect.valence} arousal={affect.arousal} />
            <DopamineBar level={affect.dopamine} />
          </div>
        </section>

        <section className="bg-zinc-900/50 rounded p-4 overflow-y-auto max-h-[80vh]">
          <MemoryFeed items={memories} />
        </section>
      </div>
    </main>
  );
}
