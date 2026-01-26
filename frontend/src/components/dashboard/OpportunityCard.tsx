"use client";

import { motion } from "framer-motion";
import { GlowingBorder } from "../shared/GlowingBorder";
import { NeonText } from "../shared/NeonText";
import { Opportunity } from "@/types/opportunity";

interface OpportunityCardProps {
  opportunity: Opportunity;
  index: number;
}

export function OpportunityCard({ opportunity, index }: OpportunityCardProps) {
  const isProfitable = opportunity.net_profit > 0;
  const isLowEdge = opportunity.edge_percent < 2;
  const edgeColor =
    opportunity.edge_percent >= 3
      ? "green"
      : opportunity.edge_percent >= 2
        ? "cyan"
        : "yellow";

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.1 }}
    >
      <GlowingBorder
        color={isProfitable ? "green" : "cyan"}
        className="p-4 hover:shadow-neon transition-shadow"
      >
        {/* Header */}
        <div className="flex items-start justify-between mb-3">
          <div className="flex-1 pr-4">
            <h3 className="text-white font-medium text-sm leading-tight line-clamp-2">
              {opportunity.market_question}
            </h3>
          </div>
          <div className="flex items-center gap-2">
            {/* Low Edge Warning Badge */}
            {isLowEdge && (
              <span className="px-2 py-1 text-xs font-bold rounded bg-neon-red/20 text-neon-red border border-neon-red/30">
                LOW EDGE
              </span>
            )}
            <span
              className={`
              px-2 py-1 text-xs font-bold rounded
              ${edgeColor === "green" ? "bg-neon-green/20 text-neon-green" : ""}
              ${edgeColor === "cyan" ? "bg-neon-cyan/20 text-neon-cyan" : ""}
              ${edgeColor === "yellow" ? "bg-neon-yellow/20 text-neon-yellow" : ""}
            `}
            >
              {opportunity.edge_percent.toFixed(2)}%
            </span>
          </div>
        </div>

        {/* Low Edge Warning Message */}
        {isLowEdge && (
          <div className="mb-3 p-2 bg-neon-red/10 border border-neon-red/20 rounded text-xs text-neon-red">
            ⚠ Edge below 2% - consider fees and slippage before trading
          </div>
        )}

        {/* Prices Grid */}
        <div className="grid grid-cols-3 gap-4 mb-3">
          <div>
            <div className="text-gray-500 text-xs mb-1">YES</div>
            <div className="text-neon-green font-mono">
              ${opportunity.yes_price.toFixed(4)}
            </div>
          </div>
          <div>
            <div className="text-gray-500 text-xs mb-1">NO</div>
            <div className="text-neon-red font-mono">
              ${opportunity.no_price.toFixed(4)}
            </div>
          </div>
          <div>
            <div className="text-gray-500 text-xs mb-1">COMBINED</div>
            <div className="text-neon-cyan font-mono">
              ${opportunity.combined_cost.toFixed(4)}
            </div>
          </div>
        </div>

        {/* Profit */}
        <div className="flex items-center justify-between pt-3 border-t border-dark-border">
          <div>
            <div className="text-gray-500 text-xs mb-1">NET PROFIT</div>
            <NeonText color="green" size="lg">
              ${opportunity.net_profit.toFixed(4)}
            </NeonText>
          </div>
          <div className="text-right">
            <div className="text-gray-500 text-xs mb-1">DETECTED</div>
            <div className="text-gray-400 text-sm">
              {new Date(opportunity.detected_at).toLocaleTimeString()}
            </div>
          </div>
        </div>

        {/* Action hint */}
        <div className="mt-3 pt-3 border-t border-dark-border">
          <div className="text-gray-500 text-xs">
            Buy YES @ ${opportunity.yes_price.toFixed(2)} + NO @ $
            {opportunity.no_price.toFixed(2)} = ${opportunity.combined_cost.toFixed(2)}
          </div>
        </div>
      </GlowingBorder>
    </motion.div>
  );
}
