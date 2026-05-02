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

// Per backend `nova_agent/decision/tot.py` publishes:
//   tot_branch (complete):    {game_id, move_idx, direction, value, reasoning, status: "complete"}
//   tot_branch (parse_error): {game_id, move_idx, direction, status: "parse_error", error}
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

export type ToTBranchData = ToTBranchCompleteData | ToTBranchParseErrorData;

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
  | { event: string; data: unknown };
