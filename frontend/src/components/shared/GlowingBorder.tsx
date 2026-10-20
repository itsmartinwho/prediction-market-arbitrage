"use client";

import { ReactNode } from "react";

interface GlowingBorderProps {
  children: ReactNode;
  color?: "cyan" | "magenta" | "green" | "red" | "yellow" | "orange";
  className?: string;
}

// The panel's accent is a thin top rule; the rest stays quiet.
const accent = {
  cyan: "border-t-neon-cyan/60",
  magenta: "border-t-neon-magenta/60",
  green: "border-t-neon-green/60",
  red: "border-t-neon-red/60",
  yellow: "border-t-neon-yellow/60",
  orange: "border-t-neon-orange/60",
};

export function GlowingBorder({ children, color = "cyan", className = "" }: GlowingBorderProps) {
  return (
    <section className={`rounded-lg border border-dark-border border-t-2 bg-dark-gray ${accent[color]} ${className}`}>
      {children}
    </section>
  );
}
