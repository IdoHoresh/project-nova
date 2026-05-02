"use client";

import { useEffect, useRef, useState } from "react";
import type {
  StreamEntry,
  DecisionEntry,
  AffectCrossingEntry,
  ModeFlipEntry,
  ToTBlockEntry,
  ToTBranchEntry,
  MemoryRecalledEntry,
  TraumaEntry,
  GameOverEntry,
} from "@/lib/stream/types";
import { truncate } from "@/lib/stream/reword";

// Soft cap on decision-text length. The LLM prompt asks for 5-15 word
// fragments, but Gemini occasionally ignores the constraint and emits
// 2-3 sentence analyses. Truncating in the viewer keeps the stream
// scannable even when the upstream prompt is ignored.
const DECISION_TEXT_MAX = 90;

interface Props {
  entries: StreamEntry[];
}

const CHIP_BY_KIND: Partial<Record<StreamEntry["kind"], { label: string; classes: string }>> = {
  affect_crossing: {
    label: "MOOD",
    classes: "bg-amber-400/15 text-amber-400",
  },
  mode_flip: {
    label: "MODE",
    classes: "bg-sky-400/15 text-sky-400",
  },
  tot_block: {
    label: "DELIBERATING",
    classes: "bg-purple-400/15 text-purple-400",
  },
  memory_recalled: {
    label: "RECALLED",
    classes: "bg-emerald-400/15 text-emerald-400",
  },
  trauma: {
    label: "TRAUMA",
    classes: "bg-red-400/20 text-red-400",
  },
  game_over: {
    label: "GAME OVER",
    classes: "bg-red-400/20 text-red-400",
  },
};

const BORDER_BY_KIND: Record<StreamEntry["kind"], string> = {
  decision: "border border-white/[0.04] bg-white/[0.02]",
  affect_crossing: "border border-white/[0.04] bg-white/[0.02]",
  mode_flip: "border border-sky-400/40 bg-sky-400/[0.06]",
  tot_block: "border border-purple-400/40 bg-purple-400/[0.06]",
  memory_recalled: "border border-emerald-400/30 bg-emerald-400/[0.04]",
  trauma: "border border-red-400/45 bg-red-400/[0.08]",
  game_over: "border-y border-red-400/40 bg-red-400/[0.04]",
};

function Chip({ label, classes }: { label: string; classes: string }) {
  return (
    <span
      className={`inline-block text-[9px] uppercase tracking-[0.1em] px-[6px] py-[1px] rounded-[3px] mr-[6px] align-middle ${classes}`}
    >
      {label}
    </span>
  );
}

function Timestamp({ ts }: { ts: string }) {
  // Render local HH:MM:SS — strip the Date prefix.
  const d = new Date(ts);
  const hh = d.getHours().toString().padStart(2, "0");
  const mm = d.getMinutes().toString().padStart(2, "0");
  const ss = d.getSeconds().toString().padStart(2, "0");
  return <span className="text-stone-600 text-[10px] mr-2">{`${hh}:${mm}:${ss} ·`}</span>;
}

function DecisionRow({ e }: { e: DecisionEntry }) {
  return (
    <li
      className={`my-[6px] py-[6px] px-[10px] rounded-[4px] animate-stream-fade ${BORDER_BY_KIND.decision}`}
      title={e.text.length > DECISION_TEXT_MAX ? e.text : undefined}
    >
      <Timestamp ts={e.ts} />
      <span>{truncate(e.text, DECISION_TEXT_MAX)}</span>
    </li>
  );
}

function AffectCrossingRow({ e }: { e: AffectCrossingEntry }) {
  const chip = CHIP_BY_KIND.affect_crossing!;
  return (
    <li className={`my-[6px] py-[6px] px-[10px] rounded-[4px] animate-stream-fade ${BORDER_BY_KIND.affect_crossing}`}>
      <Chip label={chip.label} classes={chip.classes} />
      <span>{e.text}</span>
    </li>
  );
}

function ModeFlipRow({ e }: { e: ModeFlipEntry }) {
  const chip = CHIP_BY_KIND.mode_flip!;
  return (
    <li className={`my-[6px] py-[6px] px-[10px] rounded-[4px] animate-stream-fade ${BORDER_BY_KIND.mode_flip}`}>
      <Chip label={chip.label} classes={chip.classes} />
      <span>{e.text}</span>
    </li>
  );
}

function ToTRow({ e }: { e: ToTBlockEntry }) {
  const chip = CHIP_BY_KIND.tot_block!;
  return (
    <li className={`my-[6px] py-[6px] px-[10px] rounded-[4px] animate-stream-fade ${BORDER_BY_KIND.tot_block}`}>
      <Chip label={chip.label} classes={chip.classes} />
      <span>{e.lead}</span>
      <ul className="mt-2 space-y-[2px]">
        {e.branches.map((b) => (
          <BranchRow key={b.action} branch={b} winner={e.selected?.action} />
        ))}
      </ul>
      {e.selected && <p className="mt-2">{e.selected.trailer}</p>}
    </li>
  );
}

function BranchRow({ branch, winner }: { branch: ToTBranchEntry; winner?: string }) {
  const arrow = arrowFor(branch.action);
  const isWin = branch.action === winner;
  const valueText = branch.value === null ? "—" : branch.value.toFixed(2);
  return (
    <li className={`pl-4 ${isWin ? "text-purple-300" : "text-stone-400"}`}>
      <span className="mr-1">↳</span>
      <span className="font-semibold mr-1">{arrow}</span>
      <span className="mr-1">{branch.action.replace("swipe_", "")}</span>
      <span>— {branch.reasoning}</span>{" "}
      <em>{valueText}</em>
      {isWin && <span className="ml-1">✓</span>}
    </li>
  );
}

function arrowFor(action: string): string {
  switch (action) {
    case "swipe_up": return "↑";
    case "swipe_down": return "↓";
    case "swipe_left": return "←";
    case "swipe_right": return "→";
    default: return "?";
  }
}

function MemoryRecalledRow({ e }: { e: MemoryRecalledEntry }) {
  const chip = CHIP_BY_KIND.memory_recalled!;
  return (
    <li className={`my-[6px] py-[6px] px-[10px] rounded-[4px] animate-stream-fade ${BORDER_BY_KIND.memory_recalled}`}>
      <Chip label={chip.label} classes={chip.classes} />
      <span>{e.text}</span>
    </li>
  );
}

function TraumaRow({ e }: { e: TraumaEntry }) {
  const chip = CHIP_BY_KIND.trauma!;
  return (
    <li className={`my-[6px] py-[6px] px-[10px] rounded-[4px] animate-stream-fade animate-stream-trauma ${BORDER_BY_KIND.trauma}`}>
      <Chip label={chip.label} classes={chip.classes} />
      <span>{e.text}</span>
      {e.count > 1 && <span className="ml-1 text-stone-500">× {e.count}</span>}
    </li>
  );
}

function GameOverRow({ e }: { e: GameOverEntry }) {
  const chip = CHIP_BY_KIND.game_over!;
  return (
    <li className={`my-[12px] py-[10px] px-[10px] animate-stream-fade ${BORDER_BY_KIND.game_over}`}>
      <Chip label={chip.label} classes={chip.classes} />
      <span>
        Final score {e.finalScore} · max tile {e.maxTile}
        {e.catastrophic && " · catastrophic"}
      </span>
      {e.lesson && <p className="mt-1 italic text-stone-400">Lesson: {e.lesson}</p>}
    </li>
  );
}

function Row({ entry }: { entry: StreamEntry }) {
  switch (entry.kind) {
    case "decision":         return <DecisionRow e={entry} />;
    case "affect_crossing":  return <AffectCrossingRow e={entry} />;
    case "mode_flip":        return <ModeFlipRow e={entry} />;
    case "tot_block":        return <ToTRow e={entry} />;
    case "memory_recalled":  return <MemoryRecalledRow e={entry} />;
    case "trauma":           return <TraumaRow e={entry} />;
    case "game_over":        return <GameOverRow e={entry} />;
  }
}

export function ThoughtStream({ entries }: Props) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  // "Stuck to top" = the newest entry is visible. Newest is rendered FIRST
  // (entries are reversed for display) so the natural pinned position is
  // scrollTop=0. Detach when the user scrolls down past 24px.
  const [stuckToTop, setStuckToTop] = useState(true);
  // Snapshot of entries.length the last time user was at-top. Updated only
  // in event handlers (scroll, jumpToLive) — never in effects — so render-time
  // derivation of `unseen` doesn't trip set-state-in-effect.
  const [lastSeenLength, setLastSeenLength] = useState(entries.length);

  const unseen = stuckToTop
    ? 0
    : Math.max(0, entries.length - lastSeenLength);

  // Render newest-first. The deriveStream output is chronological-oldest-first
  // (so its reducer logic stays simple). Reverse here at the presentation
  // boundary so users see the most recent thought at the top.
  const ordered = [...entries].reverse();

  // Sticky-scroll: on entries change, snap to top if currently stuck.
  useEffect(() => {
    if (!containerRef.current || !stuckToTop) return;
    containerRef.current.scrollTo({
      top: 0,
      behavior: "smooth",
    });
  }, [entries, stuckToTop]);

  function onScroll() {
    const el = containerRef.current;
    if (!el) return;
    const distanceFromTop = el.scrollTop;
    const nowStuck = distanceFromTop <= 24;
    setStuckToTop(nowStuck);
    if (nowStuck) {
      setLastSeenLength(entries.length);
    }
  }

  function jumpToLive() {
    setStuckToTop(true);
    setLastSeenLength(entries.length);
    if (containerRef.current) {
      containerRef.current.scrollTo({
        top: 0,
        behavior: "smooth",
      });
    }
  }

  if (entries.length === 0) {
    return (
      <div className="flex items-center justify-center h-full text-stone-500 text-xs">
        Waiting for nova to start thinking…
      </div>
    );
  }
  return (
    <div className="relative h-full">
      <div ref={containerRef} onScroll={onScroll} className="h-full overflow-y-auto">
        <ul className="font-mono text-[11.5px] leading-[1.55] text-stone-200 list-none p-0 m-0">
          {ordered.map((e) => (
            <Row key={e.id} entry={e} />
          ))}
        </ul>
      </div>
      {!stuckToTop && (
        <button
          type="button"
          onClick={jumpToLive}
          className="absolute top-3 right-3 text-[10px] uppercase tracking-[0.1em] px-3 py-1 rounded bg-sky-400/15 text-sky-300 border border-sky-400/30 hover:bg-sky-400/25"
        >
          ↑ jump to live{unseen > 0 ? ` (${unseen} new)` : ""}
        </button>
      )}
    </div>
  );
}
