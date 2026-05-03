"use client";
import { AnimatePresence, motion } from "framer-motion";

export type AgentMode = "react" | "tot";

export function ModeBadge({ mode }: { mode: AgentMode }) {
  const label = mode === "tot" ? "🔴 DELIBERATING" : "🟢 INTUITION";
  return (
    <AnimatePresence mode="wait">
      <motion.div
        key={mode}
        initial={{ opacity: 0, x: -10 }}
        animate={{ opacity: 1, x: 0 }}
        exit={{ opacity: 0, x: 10 }}
        transition={{ duration: 0.25 }}
        className={`inline-block px-3 py-1 rounded-full text-xs font-mono ${
          mode === "tot"
            ? "bg-red-950/60 text-red-200"
            : "bg-emerald-950/60 text-emerald-200"
        }`}
      >
        {label}
      </motion.div>
    </AnimatePresence>
  );
}
