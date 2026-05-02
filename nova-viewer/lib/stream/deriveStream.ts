import type {
  AgentEvent,
  AffectVectorDTO,
  AgentMode,
  SwipeAction,
  ToTBranchData,
  ToTSelectedData,
} from "@/lib/types";
import type {
  StreamEntry,
  DecisionEntry,
  ModeFlipEntry,
  ToTBlockEntry,
  ToTBranchEntry,
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

const TOT_LEAD = "Let me slow down and deliberate over all four moves.";
const PARSE_ERROR_REASONING = "couldn't see this clearly";

function makeToTBlock(seq: number, ts: string): ToTBlockEntry {
  return {
    kind: "tot_block",
    id: `tot_block-${seq}`,
    ts,
    lead: TOT_LEAD,
    branches: [],
  };
}

function applyBranch(block: ToTBlockEntry, data: ToTBranchData): void {
  const branch: ToTBranchEntry =
    data.status === "complete"
      ? {
          action: data.direction,
          value: data.value,
          reasoning: rewordFirstPerson(data.reasoning),
          status: "complete",
        }
      : {
          action: data.direction,
          value: null,
          reasoning: PARSE_ERROR_REASONING,
          status: "parse_error",
        };

  // De-duplicate by action: a complete branch replaces an earlier parse_error
  // (and vice versa, last write wins).
  const existingIdx = block.branches.findIndex((b) => b.action === branch.action);
  if (existingIdx >= 0) {
    block.branches[existingIdx] = branch;
  } else {
    block.branches.push(branch);
  }
}

function applySelected(block: ToTBlockEntry, data: ToTSelectedData): void {
  block.selected = {
    action: data.chosen_action,
    trailer: `Going with ${data.chosen_action.replace("swipe_", "")}.`,
  };
}

export function deriveStream(
  events: AgentEvent[],
  opts: DeriveOptions = {},
): StreamEntry[] {
  const now = opts.now ?? (() => new Date());
  const _prevAffect = opts.prevAffect ?? null;

  const entries: StreamEntry[] = [];
  let seq = 0;
  let currentMode: AgentMode | null = null;
  let openBlock: ToTBlockEntry | null = null;

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
      // Opening a fresh ToT round when entering tot mode (and on first sight of tot).
      if (next === "tot") {
        openBlock = makeToTBlock(seq++, now().toISOString());
        entries.push(openBlock);
      }
      // Leaving tot mode finalizes any open block (selected may already be set).
      if (next !== "tot") {
        openBlock = null;
      }
      currentMode = next;
      continue;
    }
    if (e.event === "tot_branch") {
      const d = e.data as ToTBranchData;
      // If we never saw a mode flip but ToT branches are arriving, open a block.
      if (!openBlock) {
        openBlock = makeToTBlock(seq++, now().toISOString());
        entries.push(openBlock);
      }
      applyBranch(openBlock, d);
      continue;
    }
    if (e.event === "tot_selected") {
      const d = e.data as ToTSelectedData;
      if (!openBlock) {
        // Same defensive open as above.
        openBlock = makeToTBlock(seq++, now().toISOString());
        entries.push(openBlock);
      }
      applySelected(openBlock, d);
      continue;
    }
    if (e.event === "decision") {
      // A non-ToT decision entry. While ToT mode is open, decisions are
      // implicit (they come out of tot_selected). Only emit a decision entry
      // when not currently inside an open block, OR when the decision's own
      // mode is "react".
      const d = e.data as {
        action: string;
        reasoning: string;
        confidence: string;
        mode?: AgentMode;
      };
      const decisionMode = (d.mode ?? currentMode) as AgentMode | null;
      if (decisionMode === "tot" && openBlock) {
        // The block already represents this move; skip the redundant decision.
        continue;
      }
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
