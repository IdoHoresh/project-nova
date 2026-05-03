"use client";

import { useMemo } from "react";

import { BrainPanel } from "./components/BrainPanel";
import { GameStream } from "./components/GameStream";
import { ModeBadge } from "./components/ModeBadge";
import { ThoughtStream } from "./components/ThoughtStream";
import { TraumaIndicator } from "./components/TraumaIndicator";
import { useNovaSocket } from "@/lib/websocket";
import { deriveStream } from "@/lib/stream/deriveStream";
import type { AffectVectorDTO, AgentMode, RetrievedMemoryDTO } from "@/lib/types";

const NEUTRAL_AFFECT: AffectVectorDTO = {
  valence: 0,
  arousal: 0.2,
  dopamine: 0,
  frustration: 0,
  anxiety: 0,
  confidence: 0.5,
};

interface Stats {
  score: number;
  move: number;
  games: number;
  best: number;
}

export default function Home() {
  const { events, connected } = useNovaSocket();

  const memories = useMemo<RetrievedMemoryDTO[]>(() => {
    for (let i = events.length - 1; i >= 0; i--) {
      const e = events[i];
      if (e.event === "memory_retrieved") {
        return e.data.items;
      }
    }
    return [];
  }, [events]);

  const affect = useMemo<AffectVectorDTO>(() => {
    for (let i = events.length - 1; i >= 0; i--) {
      const e = events[i];
      if (e.event === "affect") return e.data;
    }
    return NEUTRAL_AFFECT;
  }, [events]);

  const affectText = useMemo<string>(() => {
    for (let i = events.length - 1; i >= 0; i--) {
      const e = events[i];
      if (e.event === "decision") {
        const d = e.data;
        if (d.affect_text) return d.affect_text;
      }
    }
    return "";
  }, [events]);

  const mode = useMemo<AgentMode>(() => {
    for (let i = events.length - 1; i >= 0; i--) {
      const e = events[i];
      if (e.event === "mode") return e.data.mode;
    }
    return "react";
  }, [events]);

  const traumaActive = useMemo<boolean>(() => {
    for (let i = events.length - 1; i >= 0; i--) {
      const e = events[i];
      if (e.event === "trauma_active") {
        return e.data.active;
      }
    }
    return false;
  }, [events]);

  const stats = useMemo<Stats>(() => {
    let score = 0;
    let move = 0;
    let best = 0;
    let games = 1;
    for (const e of events) {
      if (e.event === "perception") {
        const d = e.data;
        score = d.score;
        if (d.score > best) best = d.score;
        move = d.step;
      } else if (e.event === "game_over") {
        games += 1;
      }
    }
    return { score, move, games, best };
  }, [events]);

  const streamEntries = useMemo(() => deriveStream(events), [events]);

  return (
    <main className="min-h-screen bg-[#1a1614] text-zinc-100 p-8 font-mono text-sm">
      <TraumaIndicator active={traumaActive} />
      <header className="flex justify-between items-baseline mb-4">
        <h1 className="text-2xl">Project Nova — brain panel</h1>
        <span
          className={`text-xs ${connected ? "text-emerald-400" : "text-zinc-500"}`}
        >
          {connected ? "● live" : "○ disconnected"}
        </span>
      </header>

      <div className="grid grid-cols-3 gap-8 max-h-[88vh]">
        <section className="bg-zinc-900/50 rounded p-4">
          <GameStream />
        </section>

        <section className="bg-zinc-900/50 rounded p-4 flex flex-col gap-4 min-h-0">
          <div className="flex items-center justify-between">
            <h2 className="text-sm uppercase tracking-wider text-zinc-500">
              Cognition · stream
            </h2>
            <ModeBadge mode={mode} />
          </div>
          <div className="flex-1 min-h-0">
            <ThoughtStream entries={streamEntries} />
          </div>
        </section>

        <section className="bg-zinc-900/50 rounded p-4">
          <BrainPanel
            affect={affect}
            affectText={affectText}
            memories={memories}
            score={stats.score}
            move={stats.move}
            games={stats.games}
            best={stats.best}
          />
        </section>
      </div>
    </main>
  );
}
