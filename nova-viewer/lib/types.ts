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
  | { event: string; data: unknown };
