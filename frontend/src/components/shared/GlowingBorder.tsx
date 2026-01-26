"use client";

import { motion } from "framer-motion";
import { ReactNode } from "react";

interface GlowingBorderProps {
  children: ReactNode;
  color?: "cyan" | "magenta" | "green" | "red" | "yellow" | "orange";
  className?: string;
  animate?: boolean;
}

const colorMap = {
  cyan: {
    border: "border-neon-cyan/30",
    glow: "shadow-neon",
    hoverBorder: "hover:border-neon-cyan/60",
  },
  magenta: {
    border: "border-neon-magenta/30",
    glow: "shadow-neon-magenta",
    hoverBorder: "hover:border-neon-magenta/60",
  },
  green: {
    border: "border-neon-green/30",
    glow: "shadow-neon-green",
    hoverBorder: "hover:border-neon-green/60",
  },
  red: {
    border: "border-neon-red/30",
    glow: "shadow-neon-red",
    hoverBorder: "hover:border-neon-red/60",
  },
  yellow: {
    border: "border-neon-yellow/30",
    glow: "shadow-neon-yellow",
    hoverBorder: "hover:border-neon-yellow/60",
  },
  orange: {
    border: "border-neon-orange/30",
    glow: "shadow-neon-orange",
    hoverBorder: "hover:border-neon-orange/60",
  },
};

export function GlowingBorder({
  children,
  color = "cyan",
  className = "",
  animate = true,
}: GlowingBorderProps) {
  const colors = colorMap[color];

  return (
    <motion.div
      className={`
        relative border ${colors.border} ${colors.hoverBorder}
        bg-dark-gray/50 backdrop-blur-sm rounded
        transition-all duration-300
        ${className}
      `}
      whileHover={animate ? { scale: 1.01 } : undefined}
      transition={{ type: "spring", stiffness: 400, damping: 30 }}
    >
      {children}
    </motion.div>
  );
}
