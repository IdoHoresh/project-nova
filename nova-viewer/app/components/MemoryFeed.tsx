import { MemoryCard } from "./MemoryCard";
import type { RetrievedMemoryDTO } from "@/lib/types";

export function MemoryFeed({ items }: { items: RetrievedMemoryDTO[] }) {
  return (
    <section className="space-y-2">
      <h3 className="text-sm uppercase tracking-wider text-zinc-500">
        Recalling
      </h3>
      {items.length === 0 && (
        <p className="text-xs text-zinc-600">No memories surfaced.</p>
      )}
      <div className="space-y-2">
        {items.map((m) => (
          <MemoryCard key={m.id} m={m} />
        ))}
      </div>
    </section>
  );
}
