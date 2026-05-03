"use client";
import { AnimatePresence, motion } from "framer-motion";

export function AffectLabel({ text }: { text: string }) {
  return (
    <section className="min-h-[60px]">
      <h3 className="text-sm uppercase tracking-wider text-zinc-500 mb-2">
        Feeling
      </h3>
      <AnimatePresence mode="wait">
        <motion.p
          key={text}
          initial={{ opacity: 0, y: 6 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -6 }}
          transition={{ duration: 0.4 }}
          className="text-zinc-200 text-sm leading-relaxed italic"
        >
          “{text}”
        </motion.p>
      </AnimatePresence>
    </section>
  );
}
