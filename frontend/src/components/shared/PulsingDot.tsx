"use client";

import { motion } from "framer-motion";

interface PulsingDotProps {
  color?: "green" | "red" | "cyan" | "yellow" | "magenta";
  size?: "sm" | "md" | "lg";
}

const colorClasses = {
  green: "bg-neon-green",
  red: "bg-neon-red",
  cyan: "bg-neon-cyan",
  yellow: "bg-neon-yellow",
  magenta: "bg-neon-magenta",
};

const sizeClasses = {
  sm: "w-2 h-2",
  md: "w-3 h-3",
  lg: "w-4 h-4",
};

export function PulsingDot({ color = "green", size = "md" }: PulsingDotProps) {
  return (
    <div className="relative">
      <motion.div
        className={`
          ${colorClasses[color]}
          ${sizeClasses[size]}
          rounded-full
        `}
        animate={{
          scale: [1, 1.2, 1],
          opacity: [1, 0.7, 1],
        }}
        transition={{
          duration: 2,
          repeat: Infinity,
          ease: "easeInOut",
        }}
      />
      <div
        className={`
          absolute inset-0
          ${colorClasses[color]}
          ${sizeClasses[size]}
          rounded-full
          opacity-30
          blur-sm
        `}
      />
    </div>
  );
}
