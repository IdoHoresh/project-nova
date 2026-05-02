import type {
  AgentEvent,
  AffectVectorDTO,
  AgentMode,
  GameOverData,
  RetrievedMemoryDTO,
  SwipeAction,
  ToTBranchData,
  ToTSelectedData,
} from "@/lib/types";
import type {
  StreamEntry,
  AffectCrossingEntry,
  DecisionEntry,
  GameOverEntry,
  MemoryRecalledEntry,
  ModeFlipEntry,
  ToTBlockEntry,
  ToTBranchEntry,
  TraumaEntry,
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

interface ThresholdState {
  anxietyArmed: boolean;
  valenceArmed: boolean;
  dopamineArmed: boolean;
}

const ANXIETY_FIRE = 0.6;
const ANXIETY_REARM = 0.5;
const VALENCE_FIRE = -0.4;
const VALENCE_REARM = -0.3;
const DOPAMINE_FIRE = 0.6;
const DOPAMINE_REARM = 0.5;

const CROSSING_TEXT: Record<AffectCrossingEntry["dimension"], string> = {
  anxiety_high: "Anxiety just spiked. The board feels tight.",
  valence_low: "Things are slipping. I don't like where this is going.",
  dopamine_high: "That landed better than I expected.",
};

function initThresholdState(prev: AffectVectorDTO | null): ThresholdState {
  return {
    anxietyArmed: !prev || prev.anxiety < ANXIETY_FIRE,
    valenceArmed: !prev || prev.valence > VALENCE_FIRE,
    dopamineArmed: !prev || prev.dopamine < DOPAMINE_FIRE,
  };
}

function detectCrossings(
  state: ThresholdState,
  next: AffectVectorDTO,
): AffectCrossingEntry["dimension"][] {
  const fired: AffectCrossingEntry["dimension"][] = [];
  if (state.anxietyArmed && next.anxiety > ANXIETY_FIRE) {
    fired.push("anxiety_high");
    state.anxietyArmed = false;
  } else if (!state.anxietyArmed && next.anxiety < ANXIETY_REARM) {
    state.anxietyArmed = true;
  }
  if (state.valenceArmed && next.valence < VALENCE_FIRE) {
    fired.push("valence_low");
    state.valenceArmed = false;
  } else if (!state.valenceArmed && next.valence > VALENCE_REARM) {
    state.valenceArmed = true;
  }
  if (state.dopamineArmed && next.dopamine > DOPAMINE_FIRE) {
    fired.push("dopamine_high");
    state.dopamineArmed = false;
  } else if (!state.dopamineArmed && next.dopamine < DOPAMINE_REARM) {
    state.dopamineArmed = true;
  }
  return fired;
}

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
  const thresholds = initThresholdState(_prevAffect);
  let lastTraumaActive: boolean | null = null;
  let currentTraumaEntry: TraumaEntry | null = null;

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
    if (e.event === "affect") {
      const d = e.data as AffectVectorDTO & { rpe: number; trauma_triggered: boolean };
      const fired = detectCrossings(thresholds, d);
      for (const dim of fired) {
        const entry: AffectCrossingEntry = {
          kind: "affect_crossing",
          id: `affect_crossing-${seq++}`,
          ts: now().toISOString(),
          text: CROSSING_TEXT[dim],
          dimension: dim,
        };
        entries.push(entry);
      }
      continue;
    }
    if (e.event === "memory_retrieved") {
      const d = e.data as { items: RetrievedMemoryDTO[] };
      const items = d.items;
      if (items.length === 0) continue;
      const entry: MemoryRecalledEntry = {
        kind: "memory_recalled",
        id: `memory_recalled-${seq++}`,
        ts: now().toISOString(),
        text:
          items.length === 1
            ? "I remember something from a past game."
            : `${items.length} echoes from past games surface.`,
        count: items.length,
      };
      entries.push(entry);
      continue;
    }
    if (e.event === "trauma_active") {
      const d = e.data as { active: boolean };
      const active = d.active;
      if (active && !lastTraumaActive) {
        // rising edge — new entry
        const entry: TraumaEntry = {
          kind: "trauma",
          id: `trauma-${seq++}`,
          ts: now().toISOString(),
          text: "This pattern killed me before.",
          count: 1,
        };
        entries.push(entry);
        currentTraumaEntry = entry;
      } else if (active && currentTraumaEntry) {
        // sustained — bump counter on the existing entry (mutate in place)
        currentTraumaEntry.count += 1;
      } else if (!active) {
        currentTraumaEntry = null;
      }
      lastTraumaActive = active;
      continue;
    }
    if (e.event === "game_over") {
      const d = e.data as GameOverData;
      const entry: GameOverEntry = {
        kind: "game_over",
        id: `game_over-${seq++}`,
        ts: now().toISOString(),
        finalScore: d.final_score,
        maxTile: d.max_tile,
        catastrophic: d.catastrophic,
        lesson: d.lessons.length > 0 ? d.lessons[0] : undefined,
      };
      entries.push(entry);
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

  return entries.slice(-MAX_ENTRIES);
}

export const DERIVE_MAX_ENTRIES = MAX_ENTRIES;
