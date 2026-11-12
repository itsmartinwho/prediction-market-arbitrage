import { ReactNode } from "react";

interface NeonTextProps {
  children: ReactNode;
  color?: "cyan" | "magenta" | "green" | "yellow" | "orange";
  size?: "sm" | "md" | "lg" | "xl" | "2xl";
  className?: string;
}

const colorClasses = {
  cyan: "text-gray-100",
  magenta: "text-gray-100",
  green: "text-gray-100",
  yellow: "text-gray-100",
  orange: "text-gray-100",
};

const sizeClasses = {
  sm: "text-sm",
  md: "text-base",
  lg: "text-lg",
  xl: "text-xl",
  "2xl": "text-2xl",
};

/** A clean section heading with disciplined typographic hierarchy. */
export function NeonText({ children, color = "cyan", size = "md", className = "" }: NeonTextProps) {
  return (
    <h2 className={`${colorClasses[color]} ${sizeClasses[size]} font-semibold tracking-tight ${className}`}>
      {children}
    </h2>
  );
}
