"use client";
import { motion } from "framer-motion";

export function DopamineBar({ level }: { level: number }) {
  const pct = Math.max(0, Math.min(1, level)) * 100;
  return (
    <section>
      <h3 className="text-sm uppercase tracking-wider text-zinc-500 mb-2">
        Dopamine
      </h3>
      <div className="h-32 w-3 rounded-full bg-zinc-800 relative overflow-hidden">
        <motion.div
          className="absolute bottom-0 left-0 right-0 bg-cyan-400"
          style={{ borderRadius: "9999px" }}
          initial={false}
          animate={{ height: `${pct}%` }}
          transition={{ type: "spring", stiffness: 240, damping: 20 }}
        />
      </div>
    </section>
  );
}
