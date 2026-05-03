import type {
  AffectVectorDTO,
  AgentEvent,
  RetrievedMemoryDTO,
  SwipeAction,
  ToTBranchApiErrorData,
} from "@/lib/types";

export const NEUTRAL_AFFECT: AffectVectorDTO = {
  valence: 0,
  arousal: 0.2,
  dopamine: 0,
  frustration: 0,
  anxiety: 0,
  confidence: 0.5,
};

export function decisionEv(opts: {
  action?: SwipeAction;
  reasoning?: string;
  mode?: "react" | "tot";
}): AgentEvent {
  return {
    event: "decision",
    data: {
      action: opts.action ?? "swipe_down",
      reasoning: opts.reasoning ?? "I'll consolidate down.",
      observation: "board sparse",
      confidence: "medium",
      mode: opts.mode ?? "react",
    },
  };
}

export function affectEv(partial: Partial<AffectVectorDTO> & { rpe?: number; trauma_triggered?: boolean }): AgentEvent {
  return {
    event: "affect",
    data: {
      ...NEUTRAL_AFFECT,
      ...partial,
      rpe: partial.rpe ?? 0,
      trauma_triggered: partial.trauma_triggered ?? false,
    },
  };
}

export function modeEv(mode: "react" | "tot", step = 0): AgentEvent {
  return { event: "mode", data: { mode, step } };
}

export function totBranchEv(direction: SwipeAction, value: number, reasoning: string, moveIdx = 1): AgentEvent {
  return {
    event: "tot_branch",
    data: {
      game_id: "g1",
      move_idx: moveIdx,
      direction,
      value,
      reasoning,
      status: "complete",
    },
  };
}

export function totBranchParseErrEv(direction: SwipeAction, moveIdx = 1): AgentEvent {
  return {
    event: "tot_branch",
    data: {
      game_id: "g1",
      move_idx: moveIdx,
      direction,
      status: "parse_error",
      error: "no JSON in response",
    },
  };
}

export function totBranchApiErrEv(
  direction: SwipeAction,
  moveIdx = 1,
): { event: "tot_branch"; data: ToTBranchApiErrorData } {
  return {
    event: "tot_branch",
    data: {
      game_id: "g1",
      move_idx: moveIdx,
      direction,
      status: "api_error",
      error: "RetryError: 429 quota exhausted",
    },
  };
}

export function totSelectedEv(action: SwipeAction, branchValues: Partial<Record<SwipeAction, number>>, moveIdx = 1): AgentEvent {
  return {
    event: "tot_selected",
    data: {
      game_id: "g1",
      move_idx: moveIdx,
      chosen_action: action,
      chosen_value: branchValues[action] ?? 0.5,
      branch_values: branchValues,
    },
  };
}

export function memoryRetrievedEv(items: RetrievedMemoryDTO[]): AgentEvent {
  return { event: "memory_retrieved", data: { items } };
}

export function traumaActiveEv(active: boolean): AgentEvent {
  return { event: "trauma_active", data: { active } };
}

export function gameOverEv(opts?: { finalScore?: number; lesson?: string; catastrophic?: boolean }): AgentEvent {
  return {
    event: "game_over",
    data: {
      final_score: opts?.finalScore ?? 100,
      max_tile: 64,
      catastrophic: opts?.catastrophic ?? false,
      summary: "ran out of moves",
      lessons: opts?.lesson ? [opts.lesson] : [],
    },
  };
}

export function makeMemory(overrides?: Partial<RetrievedMemoryDTO>): RetrievedMemoryDTO {
  return {
    id: overrides?.id ?? "m1",
    importance: overrides?.importance ?? 5,
    action: overrides?.action ?? "swipe_down",
    score_delta: overrides?.score_delta ?? 8,
    reasoning: overrides?.reasoning ?? null,
    tags: overrides?.tags ?? [],
    preview_grid: overrides?.preview_grid ?? [
      [2, 0, 0, 0],
      [0, 0, 0, 0],
      [0, 0, 0, 0],
      [0, 0, 0, 0],
    ],
  };
}
