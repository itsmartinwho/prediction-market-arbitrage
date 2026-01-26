"use client";

import { motion } from "framer-motion";
import { ReactNode } from "react";

interface NeonTextProps {
  children: ReactNode;
  color?: "cyan" | "magenta" | "green" | "yellow" | "orange";
  size?: "sm" | "md" | "lg" | "xl" | "2xl";
  animate?: boolean;
  className?: string;
}

const colorClasses = {
  cyan: "text-neon-cyan",
  magenta: "text-neon-magenta",
  green: "text-neon-green",
  yellow: "text-neon-yellow",
  orange: "text-neon-orange",
};

const sizeClasses = {
  sm: "text-sm",
  md: "text-base",
  lg: "text-lg",
  xl: "text-xl",
  "2xl": "text-2xl",
};

export function NeonText({
  children,
  color = "cyan",
  size = "md",
  animate = false,
  className = "",
}: NeonTextProps) {
  const Component = animate ? motion.span : "span";

  return (
    <Component
      className={`
        ${colorClasses[color]}
        ${sizeClasses[size]}
        neon-text
        font-mono font-semibold
        ${className}
      `}
      {...(animate && {
        animate: { opacity: [0.7, 1, 0.7] },
        transition: { duration: 2, repeat: Infinity },
      })}
    >
      {children}
    </Component>
  );
}
