export interface RetrievedMemoryDTO {
  id: string;
  importance: number;
  action: string;
  score_delta: number;
  reasoning: string | null;
  tags: string[];
  preview_grid: number[][];
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
      };
    }
  | { event: "memory_write"; data: { id: string; importance: number; tags?: string[] } }
  | { event: "memory_retrieved"; data: { items: RetrievedMemoryDTO[] } }
  | { event: string; data: unknown };
