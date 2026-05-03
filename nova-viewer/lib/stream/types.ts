import type { SwipeAction, AgentMode } from "@/lib/types";

export type StreamEntryKind =
  | "decision"
  | "affect_crossing"
  | "mode_flip"
  | "tot_block"
  | "memory_recalled"
  | "trauma"
  | "game_over";

interface BaseEntry {
  /** Stable id for React keys. Format: `${kind}-${seq}` where seq is monotonic per derivation. */
  id: string;
  /** ISO wall-clock timestamp when the entry was first emitted by the deriver. */
  ts: string;
  kind: StreamEntryKind;
}

export interface DecisionEntry extends BaseEntry {
  kind: "decision";
  text: string;
  action: SwipeAction;
  /** Backend emits confidence as a string ("medium", "high", or numeric-as-string). */
  confidence: string;
}

export interface AffectCrossingEntry extends BaseEntry {
  kind: "affect_crossing";
  text: string;
  /** Which dimension crossed: anxiety_high, valence_low, dopamine_high. */
  dimension: "anxiety_high" | "valence_low" | "dopamine_high";
}

export interface ModeFlipEntry extends BaseEntry {
  kind: "mode_flip";
  from: AgentMode;
  to: AgentMode;
  text: string;
}

export interface ToTBranchEntry {
  action: SwipeAction;
  /** null when the branch failed to parse. */
  value: number | null;
  /** "couldn't see this clearly" when status is parse_error. */
  reasoning: string;
  status: "pending" | "complete" | "parse_error";
}

export interface ToTBlockEntry extends BaseEntry {
  kind: "tot_block";
  lead: string;
  branches: ToTBranchEntry[];
  selected?: { action: SwipeAction; trailer: string };
}

export interface MemoryRecalledEntry extends BaseEntry {
  kind: "memory_recalled";
  text: string;
  count: number;
}

export interface TraumaEntry extends BaseEntry {
  kind: "trauma";
  text: string;
  /** Coalesced count when consecutive trauma_active events fire. Starts at 1. */
  count: number;
}

export interface GameOverEntry extends BaseEntry {
  kind: "game_over";
  finalScore: number;
  maxTile: number;
  catastrophic: boolean;
  lesson?: string;
}

export type StreamEntry =
  | DecisionEntry
  | AffectCrossingEntry
  | ModeFlipEntry
  | ToTBlockEntry
  | MemoryRecalledEntry
  | TraumaEntry
  | GameOverEntry;
