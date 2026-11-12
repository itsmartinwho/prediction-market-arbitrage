"use client";

import { ReactNode } from "react";

interface GlowingBorderProps {
  children: ReactNode;
  color?: "cyan" | "magenta" | "green" | "red" | "yellow" | "orange";
  className?: string;
}

// Disciplined quantitative surface: uniform dark slate card with subtle top rule.
const accent = {
  cyan: "border-t-neon-cyan/45",
  magenta: "border-t-neon-cyan/45",
  green: "border-t-neon-green/50",
  red: "border-t-neon-red/50",
  yellow: "border-t-neon-cyan/45",
  orange: "border-t-neon-cyan/45",
};

export function GlowingBorder({ children, color = "cyan", className = "" }: GlowingBorderProps) {
  return (
    <section className={`rounded-lg border border-dark-border border-t-2 bg-dark-gray ${accent[color]} ${className}`}>
      {children}
    </section>
  );
}
