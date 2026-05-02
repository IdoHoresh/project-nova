import type { AgentEvent, AffectVectorDTO, SwipeAction } from "@/lib/types";
import type { StreamEntry, DecisionEntry } from "./types";
import { rewordFirstPerson } from "./reword";

const MAX_ENTRIES = 100;

export interface DeriveOptions {
  prevAffect?: AffectVectorDTO | null;
  now?: () => Date;
}

export function deriveStream(
  events: AgentEvent[],
  opts: DeriveOptions = {},
): StreamEntry[] {
  const now = opts.now ?? (() => new Date());
  const _prevAffect = opts.prevAffect ?? null;

  const entries: StreamEntry[] = [];
  let seq = 0;

  for (const e of events) {
    if (e.event === "decision") {
      const d = e.data as {
        action: string;
        reasoning: string;
        confidence: string;
      };
      const action = d.action as SwipeAction;
      const entry: DecisionEntry = {
        kind: "decision",
        id: `decision-${seq++}`,
        ts: now().toISOString(),
        text: rewordFirstPerson(d.reasoning),
        action,
        confidence: d.confidence,
      };
      entries.push(entry);
    }
  }

  void _prevAffect;
  return entries.slice(-MAX_ENTRIES);
}

export const DERIVE_MAX_ENTRIES = MAX_ENTRIES;
