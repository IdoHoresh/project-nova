import type {
  AgentEvent,
  AffectVectorDTO,
  AgentMode,
  SwipeAction,
} from "@/lib/types";
import type {
  StreamEntry,
  DecisionEntry,
  ModeFlipEntry,
} from "./types";
import { rewordFirstPerson } from "./reword";

const MAX_ENTRIES = 100;

export interface DeriveOptions {
  prevAffect?: AffectVectorDTO | null;
  now?: () => Date;
}

const MODE_FLIP_TEXT: Record<`${AgentMode}->${AgentMode}`, string> = {
  "react->tot": "Things just got harder. I'm going to slow down and deliberate.",
  "tot->react": "Pressure's off. Back to gut moves.",
  "react->react": "",
  "tot->tot": "",
};

export function deriveStream(
  events: AgentEvent[],
  opts: DeriveOptions = {},
): StreamEntry[] {
  const now = opts.now ?? (() => new Date());
  const _prevAffect = opts.prevAffect ?? null;

  const entries: StreamEntry[] = [];
  let seq = 0;
  let currentMode: AgentMode | null = null;

  for (const e of events) {
    if (e.event === "mode") {
      const d = e.data as { mode: AgentMode; step?: number };
      const next = d.mode;
      if (currentMode !== null && next !== currentMode) {
        const entry: ModeFlipEntry = {
          kind: "mode_flip",
          id: `mode_flip-${seq++}`,
          ts: now().toISOString(),
          from: currentMode,
          to: next,
          text: MODE_FLIP_TEXT[`${currentMode}->${next}`],
        };
        entries.push(entry);
      }
      currentMode = next;
      continue;
    }
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
      continue;
    }
  }

  void _prevAffect;
  return entries.slice(-MAX_ENTRIES);
}

export const DERIVE_MAX_ENTRIES = MAX_ENTRIES;
