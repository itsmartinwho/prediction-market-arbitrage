import { ReactNode } from "react";

interface NeonTextProps {
  children: ReactNode;
  color?: "cyan" | "magenta" | "green" | "yellow" | "orange";
  size?: "sm" | "md" | "lg" | "xl" | "2xl";
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

/** A section heading in its panel's accent colour. */
export function NeonText({ children, color = "cyan", size = "md", className = "" }: NeonTextProps) {
  return (
    <h2 className={`${colorClasses[color]} ${sizeClasses[size]} font-semibold tracking-tight ${className}`}>
      {children}
    </h2>
  );
}
