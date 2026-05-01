"use client";
import { motion } from "framer-motion";

interface Props {
  valence: number;
  arousal: number;
}

function moodColor(valence: number, arousal: number): string {
  const hue = valence > 0 ? 140 : 0;
  const sat = 40 + arousal * 50;
  const lit = 50 - Math.abs(valence) * 10;
  return `hsl(${hue} ${sat}% ${lit}%)`;
}

export function MoodGauge({ valence, arousal }: Props) {
  const r = 70;
  const cx = 80;
  const cy = 80;
  const x = cx + valence * r;
  const y = cy + (1 - arousal * 2) * r;
  const color = moodColor(valence, arousal);

  return (
    <section>
      <h3 className="text-sm uppercase tracking-wider text-zinc-500 mb-2">
        Mood
      </h3>
      <svg width="160" height="160" className="block">
        <circle
          cx={cx}
          cy={cy}
          r={r}
          fill="none"
          stroke="#3f3f46"
          strokeWidth="1"
        />
        <line
          x1={cx - r}
          y1={cy}
          x2={cx + r}
          y2={cy}
          stroke="#3f3f46"
          strokeWidth="0.5"
        />
        <line
          x1={cx}
          y1={cy - r}
          x2={cx}
          y2={cy + r}
          stroke="#3f3f46"
          strokeWidth="0.5"
        />
        <motion.circle
          cx={x}
          cy={y}
          r={10}
          fill={color}
          initial={false}
          animate={{ cx: x, cy: y, fill: color }}
          transition={{ type: "spring", stiffness: 80, damping: 18 }}
        />
        <text
          x={cx}
          y={12}
          fill="#71717a"
          fontSize="10"
          textAnchor="middle"
        >
          arousal
        </text>
        <text x={cx + r + 4} y={cy + 4} fill="#71717a" fontSize="10">
          +val
        </text>
      </svg>
    </section>
  );
}
