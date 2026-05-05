export interface RetrievedMemoryDTO {
  id: string;
  importance: number;
  action: string;
  score_delta: number;
  reasoning: string | null;
  tags: string[];
  preview_grid: number[][];
}

export interface AffectVectorDTO {
  valence: number;
  arousal: number;
  dopamine: number;
  frustration: number;
  anxiety: number;
  confidence: number;
}

export type AgentMode = "react" | "tot";

export type SwipeAction =
  | "swipe_up"
  | "swipe_down"
  | "swipe_left"
  | "swipe_right";

// Per backend `nova_agent/decision/baseline.py` publishes (Task 6 telemetry):
//   bot_call_attempt:      {trial, move_index, attempt_n}
//   bot_call_success:      {trial, move_index, action, latency_ms, prompt_tokens, completion_tokens}
//   bot_call_api_error:    {trial, move_index, error_type, attempt_n}
//   bot_call_parse_failure:{trial, move_index, raw_response_excerpt, attempt_n}
//   bot_trial_aborted:     {trial, reason, last_move_index}
export interface BotCallAttemptData {
  trial: number;
  move_index: number;
  attempt_n: number;
}

export interface BotCallSuccessData {
  trial: number;
  move_index: number;
  action: string;
  latency_ms: number;
  prompt_tokens: number;
  completion_tokens: number;
}

export interface BotCallApiErrorData {
  trial: number;
  move_index: number;
  error_type: string;
  attempt_n: number;
}

export interface BotCallParseFailureData {
  trial: number;
  move_index: number;
  raw_response_excerpt: string;
  attempt_n: number;
}

export interface BotTrialAbortedData {
  trial: number;
  reason: "api_error" | "parse_failure";
  last_move_index: number;
}

// Per backend `nova_agent/decision/tot.py` publishes:
//   tot_branch (complete):    {game_id, move_idx, direction, value, reasoning, status: "complete"}
//   tot_branch (parse_error): {game_id, move_idx, direction, status: "parse_error", error}
//   tot_branch (api_error):   {game_id, move_idx, direction, status: "api_error", error}
//   tot_selected:             {game_id, move_idx, chosen_action, chosen_value, branch_values}
// And `nova_agent/main.py` publishes:
//   game_over: {final_score, max_tile, catastrophic, summary, lessons: string[]}
export interface ToTBranchCompleteData {
  game_id: string | null;
  move_idx: number | null;
  direction: SwipeAction;
  value: number;
  reasoning: string;
  status: "complete";
}

export interface ToTBranchParseErrorData {
  game_id: string | null;
  move_idx: number | null;
  direction: SwipeAction;
  status: "parse_error";
  error: string;
}

export interface ToTBranchApiErrorData {
  game_id: string | null;
  move_idx: number | null;
  direction: SwipeAction;
  status: "api_error";
  error: string;
}

export type ToTBranchData =
  | ToTBranchCompleteData
  | ToTBranchParseErrorData
  | ToTBranchApiErrorData;

export interface ToTSelectedData {
  game_id: string | null;
  move_idx: number | null;
  chosen_action: SwipeAction;
  chosen_value: number;
  branch_values: Partial<Record<SwipeAction, number>>;
}

export interface GameOverData {
  final_score: number;
  max_tile: number;
  catastrophic: boolean;
  summary: string;
  lessons: string[];
}

export type AgentEvent =
  | { event: "perception"; data: { score: number; step: number; grid?: number[][] } }
  | {
      event: "decision";
      data: {
        action: string;
        reasoning: string;
        observation: string;
        confidence: string;
        affect_text?: string;
        mode?: AgentMode;
      };
    }
  | {
      event: "affect";
      data: AffectVectorDTO & { rpe: number; trauma_triggered: boolean };
    }
  | { event: "memory_write"; data: { id: string; importance: number; tags?: string[] } }
  | { event: "memory_retrieved"; data: { items: RetrievedMemoryDTO[] } }
  | { event: "mode"; data: { mode: AgentMode; step?: number } }
  | { event: "trauma_active"; data: { active: boolean } }
  | { event: "tot_branch"; data: ToTBranchData }
  | { event: "tot_selected"; data: ToTSelectedData }
  | { event: "game_over"; data: GameOverData }
  | { event: "bot_call_attempt"; data: BotCallAttemptData }
  | { event: "bot_call_success"; data: BotCallSuccessData }
  | { event: "bot_call_api_error"; data: BotCallApiErrorData }
  | { event: "bot_call_parse_failure"; data: BotCallParseFailureData }
  | { event: "bot_trial_aborted"; data: BotTrialAbortedData };
