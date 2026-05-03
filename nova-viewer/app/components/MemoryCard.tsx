import type { RetrievedMemoryDTO } from "@/lib/types";

export function MemoryCard({ m }: { m: RetrievedMemoryDTO }) {
  const isTrauma = m.tags.includes("trauma") || m.tags.includes("aversive");
  return (
    <div
      className={`rounded-lg p-3 text-xs border ${
        isTrauma
          ? "border-red-900 bg-red-950/30"
          : "border-zinc-800 bg-zinc-900/40"
      }`}
    >
      <div className="flex justify-between items-start mb-1">
        <span className="text-cyan-400 font-mono">{m.action}</span>
        <span
          className={`px-2 py-0.5 rounded text-[10px] ${
            m.importance >= 7 ? "bg-red-900/60" : "bg-zinc-700/60"
          }`}
        >
          {m.importance}/10
        </span>
      </div>
      <div className="text-zinc-400 line-clamp-2">{m.reasoning ?? "—"}</div>
      {m.tags.length > 0 && (
        <div className="flex gap-1 mt-1">
          {m.tags.map((t) => (
            <span key={t} className="text-[10px] text-zinc-500">
              #{t}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}
