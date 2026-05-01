interface Props {
  score: number;
  move: number;
  games: number;
  best: number;
}

export function StatsFooter({ score, move, games, best }: Props) {
  return (
    <footer className="text-xs text-zinc-500 border-t border-zinc-800 pt-2 flex justify-between">
      <span>Score {score}</span>
      <span>Move {move}</span>
      <span>Games {games}</span>
      <span>Best {best}</span>
    </footer>
  );
}
