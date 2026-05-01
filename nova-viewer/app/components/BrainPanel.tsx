import { AffectLabel } from "./AffectLabel";
import { DopamineBar } from "./DopamineBar";
import { MemoryFeed } from "./MemoryFeed";
import { MoodGauge } from "./MoodGauge";
import { StatsFooter } from "./StatsFooter";
import type {
  AffectVectorDTO,
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
}

export function BrainPanel({
  affect,
  affectText,
  memories,
  score,
  move,
  games,
  best,
}: Props) {
  return (
    <div className="flex flex-col gap-6 h-full">
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
