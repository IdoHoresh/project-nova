import type { AgentEvent, AffectVectorDTO } from "@/lib/types";
import type { StreamEntry } from "./types";

const MAX_ENTRIES = 100;

export interface DeriveOptions {
  /**
   * The most recent affect vector seen *before* the events array. Used so the
   * deriver can detect threshold crossings even when the very first event in
   * the array is the one that crosses. Pass `null` on the first call.
   */
  prevAffect?: AffectVectorDTO | null;
  /** Override only for tests. */
  now?: () => Date;
}

export function deriveStream(
  events: AgentEvent[],
  opts: DeriveOptions = {},
): StreamEntry[] {
  const _now = opts.now ?? (() => new Date());
  const _prevAffect = opts.prevAffect ?? null;
  // Behavior added in subsequent tasks. For now, return empty so the file
  // type-checks. Callers will get an empty stream until Task 5b lands.
  void events;
  void _now;
  void _prevAffect;
  return [] satisfies StreamEntry[];
}

export const DERIVE_MAX_ENTRIES = MAX_ENTRIES;
