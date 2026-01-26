"use client";

import { useQuery } from "@tanstack/react-query";
import { motion, AnimatePresence } from "framer-motion";
import { GlowingBorder } from "../shared/GlowingBorder";
import { NeonText } from "../shared/NeonText";
import { PulsingDot } from "../shared/PulsingDot";
import { OpportunityCard } from "./OpportunityCard";
import { Opportunity } from "@/types/opportunity";
import { fetchArbitrageDiagnostics } from "@/lib/api";
import { ScanDiagnostics } from "@/types/market";

interface OpportunityFeedProps {
  opportunities: Opportunity[];
  isConnected: boolean;
  lastUpdate: string | null;
}

function DiagnosticsPanel({ diagnostics }: { diagnostics: ScanDiagnostics }) {
  const total = diagnostics.total_markets;
  const analyzed = total - diagnostics.filtered_not_binary - diagnostics.filtered_no_tokens;

  return (
    <div className="bg-dark-surface rounded-lg p-4 mb-4 border border-dark-border">
      <div className="text-xs text-gray-400 mb-3 font-semibold">
        SCAN DIAGNOSTICS
      </div>

      <div className="grid grid-cols-2 gap-4 text-xs">
        {/* Left Column */}
        <div className="space-y-2">
          <div className="flex justify-between">
            <span className="text-gray-500">Markets Fetched:</span>
            <span className="text-neon-cyan font-mono">{total}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-500">Binary Markets:</span>
            <span className="text-neon-cyan font-mono">{analyzed}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-500">With Prices:</span>
            <span className="text-neon-cyan font-mono">
              {analyzed - diagnostics.filtered_no_clob_liquidity}
            </span>
          </div>
        </div>

        {/* Right Column */}
        <div className="space-y-2">
          <div className="flex justify-between">
            <span className="text-gray-500">Not Profitable:</span>
            <span className="text-gray-400 font-mono">
              {diagnostics.filtered_not_profitable}
            </span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-500">Below {diagnostics.threshold_percent}% Threshold:</span>
            <span className="text-gray-400 font-mono">
              {diagnostics.filtered_below_threshold}
            </span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-500">Gamma Fallback Used:</span>
            <span className="text-neon-yellow font-mono">
              {diagnostics.used_gamma_fallback}
            </span>
          </div>
        </div>
      </div>

      {/* Summary */}
      <div className="mt-3 pt-3 border-t border-dark-border">
        <div className="flex items-center justify-between">
          <span className="text-xs text-gray-400">
            Result: {analyzed} markets analyzed, {diagnostics.opportunities_found} opportunities found
          </span>
          {diagnostics.filtered_not_profitable > 0 && (
            <span className="text-xs text-gray-500">
              (Most markets are efficiently priced)
            </span>
          )}
        </div>
      </div>
    </div>
  );
}

export function OpportunityFeed({
  opportunities,
  isConnected,
  lastUpdate,
}: OpportunityFeedProps) {
  const { data: diagnostics } = useQuery<ScanDiagnostics>({
    queryKey: ["arbitrage-diagnostics"],
    queryFn: fetchArbitrageDiagnostics,
    refetchInterval: 10000, // Every 10 seconds
  });

  return (
    <GlowingBorder className="p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <NeonText color="cyan" size="lg">
            ARBITRAGE SCANNER
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

      {/* Diagnostics Panel - always show when no opportunities */}
      {opportunities.length === 0 && diagnostics && (
        <DiagnosticsPanel diagnostics={diagnostics} />
      )}

      {/* Opportunities List */}
      {opportunities.length === 0 ? (
        <div className="text-center py-8">
          <motion.div
            animate={{ opacity: [0.5, 1, 0.5] }}
            transition={{ duration: 2, repeat: Infinity }}
          >
            <NeonText color="cyan" size="lg">
              SCANNING FOR OPPORTUNITIES...
            </NeonText>
          </motion.div>
          <p className="text-gray-500 mt-3 text-sm max-w-md mx-auto">
            No arbitrage opportunities at current prices.
            Markets on Polymarket are typically efficiently priced,
            so opportunities are rare (but they do occur!).
          </p>
          <p className="text-gray-600 mt-2 text-xs">
            Scanner checks all {diagnostics?.total_markets || "active"} markets every 5 seconds
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
            <span className="text-neon-cyan">HOW IT WORKS:</span> Buy YES + NO for combined cost.
            One always wins, paying $1.00. Profit = $1.00 - cost - 2% fee.
          </p>
          <p className="mt-1">
            <span className="text-neon-yellow">THRESHOLD:</span> Only showing opportunities
            with &gt;{diagnostics?.threshold_percent || 1}% edge after fees.
          </p>
        </div>
      </div>
    </GlowingBorder>
  );
}
