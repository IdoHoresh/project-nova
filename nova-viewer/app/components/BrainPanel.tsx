import { AffectLabel } from "./AffectLabel";
import { DopamineBar } from "./DopamineBar";
import { MemoryFeed } from "./MemoryFeed";
import { ModeBadge } from "./ModeBadge";
import { MoodGauge } from "./MoodGauge";
import { StatsFooter } from "./StatsFooter";
import type {
  AffectVectorDTO,
  AgentMode,
  RetrievedMemoryDTO,
} from "@/lib/types";

interface Props {
  affect: AffectVectorDTO;
  affectText: string;
  memories: RetrievedMemoryDTO[];
  score: number;
  move: number;
  games: number;
  best: number;
  mode: AgentMode;
}

export function BrainPanel({
  affect,
  affectText,
  memories,
  score,
  move,
  games,
  best,
  mode,
}: Props) {
  return (
    <div className="flex flex-col gap-6 h-full">
      <div className="flex items-center justify-between">
        <h2 className="text-sm uppercase tracking-wider text-zinc-500">
          Cognition
        </h2>
        <ModeBadge mode={mode} />
      </div>
      <AffectLabel text={affectText} />
      <div className="flex items-start gap-8">
        <MoodGauge valence={affect.valence} arousal={affect.arousal} />
        <DopamineBar level={affect.dopamine} />
      </div>
      <div className="flex-1 overflow-y-auto">
        <MemoryFeed items={memories} />
      </div>
      <StatsFooter score={score} move={move} games={games} best={best} />
    </div>
  );
}
