"use client";

import { motion, AnimatePresence } from "framer-motion";
import { GlowingBorder } from "../shared/GlowingBorder";
import { NeonText } from "../shared/NeonText";
import { PulsingDot } from "../shared/PulsingDot";
import { OpportunityCard } from "./OpportunityCard";
import { Opportunity } from "@/types/opportunity";

interface OpportunityFeedProps {
  opportunities: Opportunity[];
  isConnected: boolean;
  lastUpdate: string | null;
}

export function OpportunityFeed({
  opportunities,
  isConnected,
  lastUpdate,
}: OpportunityFeedProps) {
  return (
    <GlowingBorder className="p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <NeonText color="cyan" size="lg">
            LIVE OPPORTUNITIES
          </NeonText>
          {isConnected && <PulsingDot color="green" size="sm" />}
        </div>
        <div className="text-gray-500 text-sm">
          {opportunities.length} active
          {lastUpdate && (
            <span className="ml-2">
              | Updated {new Date(lastUpdate).toLocaleTimeString()}
            </span>
          )}
        </div>
      </div>

      {/* Opportunities List */}
      {opportunities.length === 0 ? (
        <div className="text-center py-12">
          <motion.div
            animate={{ opacity: [0.5, 1, 0.5] }}
            transition={{ duration: 2, repeat: Infinity }}
          >
            <NeonText color="cyan" size="lg">
              SCANNING FOR OPPORTUNITIES...
            </NeonText>
          </motion.div>
          <p className="text-gray-500 mt-2 text-sm">
            No arbitrage opportunities detected at current prices.
            <br />
            The scanner checks all active markets every 5 seconds.
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          <AnimatePresence>
            {opportunities.map((opp, index) => (
              <OpportunityCard
                key={opp.id}
                opportunity={opp}
                index={index}
              />
            ))}
          </AnimatePresence>
        </div>
      )}

      {/* Footer Info */}
      <div className="mt-6 pt-4 border-t border-dark-border">
        <div className="text-gray-500 text-xs">
          <p>
            <span className="text-neon-cyan">TIP:</span> Opportunities with{" "}
            <span className="text-neon-green">&gt;2.5% edge</span> are
            typically profitable after Polymarket&apos;s 2% fee.
          </p>
          <p className="mt-1">
            Combined cost = YES ask + NO ask. Profit = $1.00 - combined - fees.
          </p>
        </div>
      </div>
    </GlowingBorder>
  );
}
