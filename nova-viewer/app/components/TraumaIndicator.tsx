"use client";
import { motion } from "framer-motion";

export function TraumaIndicator({ active }: { active: boolean }) {
  return (
    <motion.div
      aria-hidden
      className="pointer-events-none fixed inset-0"
      style={{ boxShadow: "inset 0 0 60px rgba(220,38,38,0.5)" }}
      initial={{ opacity: 0 }}
      animate={{ opacity: active ? 0.6 : 0 }}
      transition={{
        duration: 1.2,
        repeat: active ? Infinity : 0,
        repeatType: "reverse",
      }}
    />
  );
}
