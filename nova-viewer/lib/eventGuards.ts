import type {
  AffectVectorDTO,
  AgentEvent,
  AgentMode,
  BotCallApiErrorData,
  BotCallAttemptData,
  BotCallParseFailureData,
  BotCallSuccessData,
  BotTrialAbortedData,
  GameOverData,
  RetrievedMemoryDTO,
  SwipeAction,
  ToTBranchApiErrorData,
  ToTBranchCompleteData,
  ToTBranchData,
  ToTBranchParseErrorData,
  ToTSelectedData,
} from "./types";

// Narrow `unknown` to a plain object record with string keys. This is the
// foundation every predicate below rests on — once a value is known to be a
// non-null object, indexed access is safe.
function isRecord(v: unknown): v is Record<string, unknown> {
  return typeof v === "object" && v !== null && !Array.isArray(v);
}

function isString(v: unknown): v is string {
  return typeof v === "string";
}

function isNumber(v: unknown): v is number {
  return typeof v === "number" && Number.isFinite(v);
}

function isBoolean(v: unknown): v is boolean {
  return typeof v === "boolean";
}

function isStringOrNull(v: unknown): v is string | null {
  return v === null || isString(v);
}

function isNumberOrNull(v: unknown): v is number | null {
  return v === null || isNumber(v);
}

const SWIPE_ACTIONS: ReadonlySet<string> = new Set([
  "swipe_up",
  "swipe_down",
  "swipe_left",
  "swipe_right",
]);

export function isSwipeAction(v: unknown): v is SwipeAction {
  return isString(v) && SWIPE_ACTIONS.has(v);
}

export function isAgentMode(v: unknown): v is AgentMode {
  return v === "react" || v === "tot";
}

// `AffectVectorDTO` is referenced via the intersection in `isAffectEventData`'s
// return predicate; no standalone `isAffectVector` is needed because no other
// event ships a bare AffectVector payload. If one is added later, restore the
// thin wrapper around `hasAffectVectorFields`.
function hasAffectVectorFields(v: Record<string, unknown>): boolean {
  return (
    isNumber(v.valence) &&
    isNumber(v.arousal) &&
    isNumber(v.dopamine) &&
    isNumber(v.frustration) &&
    isNumber(v.anxiety) &&
    isNumber(v.confidence)
  );
}

function isPerceptionData(
  v: unknown,
): v is { score: number; step: number; grid?: number[][] } {
  if (!isRecord(v)) return false;
  if (!isNumber(v.score) || !isNumber(v.step)) return false;
  if (v.grid !== undefined) {
    if (!Array.isArray(v.grid)) return false;
    for (const row of v.grid) {
      if (!Array.isArray(row)) return false;
      for (const cell of row) if (!isNumber(cell)) return false;
    }
  }
  return true;
}

function isDecisionData(v: unknown): v is {
  action: string;
  reasoning: string;
  observation: string;
  confidence: string;
  affect_text?: string;
  mode?: AgentMode;
} {
  if (!isRecord(v)) return false;
  if (!isString(v.action)) return false;
  if (!isString(v.reasoning)) return false;
  if (!isString(v.observation)) return false;
  if (!isString(v.confidence)) return false;
  if (v.affect_text !== undefined && !isString(v.affect_text)) return false;
  if (v.mode !== undefined && !isAgentMode(v.mode)) return false;
  return true;
}

function isAffectEventData(
  v: unknown,
): v is AffectVectorDTO & { rpe: number; trauma_triggered: boolean } {
  if (!isRecord(v)) return false;
  if (!hasAffectVectorFields(v)) return false;
  return isNumber(v.rpe) && isBoolean(v.trauma_triggered);
}

function isMemoryWriteData(
  v: unknown,
): v is { id: string; importance: number; tags?: string[] } {
  if (!isRecord(v)) return false;
  if (!isString(v.id) || !isNumber(v.importance)) return false;
  if (v.tags !== undefined) {
    if (!Array.isArray(v.tags)) return false;
    for (const t of v.tags) if (!isString(t)) return false;
  }
  return true;
}

function isRetrievedMemoryItem(v: unknown): v is RetrievedMemoryDTO {
  if (!isRecord(v)) return false;
  if (!isString(v.id) || !isNumber(v.importance) || !isString(v.action))
    return false;
  if (!isNumber(v.score_delta)) return false;
  if (!isStringOrNull(v.reasoning)) return false;
  if (!Array.isArray(v.tags)) return false;
  for (const t of v.tags) if (!isString(t)) return false;
  if (!Array.isArray(v.preview_grid)) return false;
  for (const row of v.preview_grid) {
    if (!Array.isArray(row)) return false;
    for (const cell of row) if (!isNumber(cell)) return false;
  }
  return true;
}

function isMemoryRetrievedData(
  v: unknown,
): v is { items: RetrievedMemoryDTO[] } {
  if (!isRecord(v)) return false;
  if (!Array.isArray(v.items)) return false;
  for (const item of v.items) if (!isRetrievedMemoryItem(item)) return false;
  return true;
}

function isModeData(v: unknown): v is { mode: AgentMode; step?: number } {
  if (!isRecord(v)) return false;
  if (!isAgentMode(v.mode)) return false;
  if (v.step !== undefined && !isNumber(v.step)) return false;
  return true;
}

function isTraumaActiveData(v: unknown): v is { active: boolean } {
  return isRecord(v) && isBoolean(v.active);
}

function isToTBranchComplete(v: unknown): v is ToTBranchCompleteData {
  if (!isRecord(v)) return false;
  return (
    v.status === "complete" &&
    isStringOrNull(v.game_id) &&
    isNumberOrNull(v.move_idx) &&
    isSwipeAction(v.direction) &&
    isNumber(v.value) &&
    isString(v.reasoning)
  );
}

function isToTBranchParseError(v: unknown): v is ToTBranchParseErrorData {
  if (!isRecord(v)) return false;
  return (
    v.status === "parse_error" &&
    isStringOrNull(v.game_id) &&
    isNumberOrNull(v.move_idx) &&
    isSwipeAction(v.direction) &&
    isString(v.error)
  );
}

function isToTBranchApiError(v: unknown): v is ToTBranchApiErrorData {
  if (!isRecord(v)) return false;
  return (
    v.status === "api_error" &&
    isStringOrNull(v.game_id) &&
    isNumberOrNull(v.move_idx) &&
    isSwipeAction(v.direction) &&
    isString(v.error)
  );
}

function isToTBranchData(v: unknown): v is ToTBranchData {
  return (
    isToTBranchComplete(v) ||
    isToTBranchParseError(v) ||
    isToTBranchApiError(v)
  );
}

function isToTSelectedData(v: unknown): v is ToTSelectedData {
  if (!isRecord(v)) return false;
  if (!isStringOrNull(v.game_id) || !isNumberOrNull(v.move_idx)) return false;
  if (!isSwipeAction(v.chosen_action) || !isNumber(v.chosen_value))
    return false;
  if (!isRecord(v.branch_values)) return false;
  // Allowlist guard: rejects __proto__ / constructor keys and unknown directions.
  for (const [k, val] of Object.entries(v.branch_values)) {
    if (!isSwipeAction(k)) return false;
    if (!isNumber(val)) return false;
  }
  return true;
}

function isGameOverData(v: unknown): v is GameOverData {
  if (!isRecord(v)) return false;
  if (!isNumber(v.final_score) || !isNumber(v.max_tile)) return false;
  if (!isBoolean(v.catastrophic) || !isString(v.summary)) return false;
  if (!Array.isArray(v.lessons)) return false;
  for (const l of v.lessons) if (!isString(l)) return false;
  return true;
}

function isBotCallAttemptData(v: unknown): v is BotCallAttemptData {
  if (!isRecord(v)) return false;
  return isNumber(v.trial) && isNumber(v.move_index) && isNumber(v.attempt_n);
}

function isBotCallSuccessData(v: unknown): v is BotCallSuccessData {
  if (!isRecord(v)) return false;
  return (
    isNumber(v.trial) &&
    isNumber(v.move_index) &&
    isString(v.action) &&
    isNumber(v.latency_ms) &&
    isNumber(v.prompt_tokens) &&
    isNumber(v.completion_tokens)
  );
}

function isBotCallApiErrorData(v: unknown): v is BotCallApiErrorData {
  if (!isRecord(v)) return false;
  return (
    isNumber(v.trial) &&
    isNumber(v.move_index) &&
    isString(v.error_type) &&
    isNumber(v.attempt_n)
  );
}

function isBotCallParseFailureData(v: unknown): v is BotCallParseFailureData {
  if (!isRecord(v)) return false;
  return (
    isNumber(v.trial) &&
    isNumber(v.move_index) &&
    isString(v.raw_response_excerpt) &&
    isNumber(v.excerpt_length) &&
    isNumber(v.attempt_n)
  );
}

function isBotTrialAbortedData(v: unknown): v is BotTrialAbortedData {
  if (!isRecord(v)) return false;
  return (
    isNumber(v.trial) &&
    (v.reason === "api_error" || v.reason === "parse_failure") &&
    isNumber(v.last_move_index)
  );
}

// Top-level dispatcher. Returns the validated AgentEvent or null. Caller
// (useNovaSocket) is responsible for logging dropped frames.
export function parseAgentEvent(raw: unknown): AgentEvent | null {
  if (!isRecord(raw)) return null;
  const eventName = raw.event;
  const data = raw.data;
  if (!isString(eventName)) return null;

  switch (eventName) {
    case "perception":
      return isPerceptionData(data) ? { event: "perception", data } : null;
    case "decision":
      return isDecisionData(data) ? { event: "decision", data } : null;
    case "affect":
      return isAffectEventData(data) ? { event: "affect", data } : null;
    case "memory_write":
      return isMemoryWriteData(data) ? { event: "memory_write", data } : null;
    case "memory_retrieved":
      return isMemoryRetrievedData(data)
        ? { event: "memory_retrieved", data }
        : null;
    case "mode":
      return isModeData(data) ? { event: "mode", data } : null;
    case "trauma_active":
      return isTraumaActiveData(data)
        ? { event: "trauma_active", data }
        : null;
    case "tot_branch":
      return isToTBranchData(data) ? { event: "tot_branch", data } : null;
    case "tot_selected":
      return isToTSelectedData(data) ? { event: "tot_selected", data } : null;
    case "game_over":
      return isGameOverData(data) ? { event: "game_over", data } : null;
    case "bot_call_attempt":
      return isBotCallAttemptData(data)
        ? { event: "bot_call_attempt", data }
        : null;
    case "bot_call_success":
      return isBotCallSuccessData(data)
        ? { event: "bot_call_success", data }
        : null;
    case "bot_call_api_error":
      return isBotCallApiErrorData(data)
        ? { event: "bot_call_api_error", data }
        : null;
    case "bot_call_parse_failure":
      return isBotCallParseFailureData(data)
        ? { event: "bot_call_parse_failure", data }
        : null;
    case "bot_trial_aborted":
      return isBotTrialAbortedData(data)
        ? { event: "bot_trial_aborted", data }
        : null;
    default:
      // Unknown event names are dropped. The catch-all used to swallow these
      // silently; now they're an explicit drop. If the agent gains a new
      // event type, both lib/types.ts and this switch must be updated in
      // the same PR (per nova-viewer/AGENTS.md "Bus contract" rule).
      return null;
  }
}
