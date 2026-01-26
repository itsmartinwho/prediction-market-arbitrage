"use client";

import { useQuery } from "@tanstack/react-query";
import { motion, AnimatePresence } from "framer-motion";
import { GlowingBorder } from "../shared/GlowingBorder";
import { NeonText } from "../shared/NeonText";
import { PulsingDot } from "../shared/PulsingDot";
import { fetchWhaleActivity } from "@/lib/api";
import { WhaleActivity } from "@/types/whale";

function formatUSD(value: number): string {
  if (value >= 1000000) {
    return `$${(value / 1000000).toFixed(2)}M`;
  }
  if (value >= 1000) {
    return `$${(value / 1000).toFixed(1)}K`;
  }
  return `$${value.toFixed(0)}`;
}

function formatTimeAgo(timestamp: string): string {
  const now = new Date();
  const then = new Date(timestamp);
  const diffMs = now.getTime() - then.getTime();

  const mins = Math.floor(diffMs / 60000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins}m ago`;

  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours}h ago`;

  const days = Math.floor(hours / 24);
  return `${days}d ago`;
}

function TradeCard({ trade, index }: { trade: WhaleActivity; index: number }) {
  const isBuy = trade.action === "BUY";

  return (
    <motion.a
      href={trade.polymarket_url}
      target="_blank"
      rel="noopener noreferrer"
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: index * 0.03 }}
      className="block p-4 bg-dark-surface rounded-lg border border-dark-border
                 hover:border-neon-magenta/40 transition-all duration-200 group"
    >
      {/* Header: Trader + Action + Time */}
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-neon-magenta font-semibold text-sm">
            {trade.trader_name}
          </span>
          <span
            className={`text-xs font-mono px-2 py-0.5 rounded ${
              isBuy
                ? "bg-neon-green/20 text-neon-green"
                : "bg-neon-red/20 text-neon-red"
            }`}
          >
            {trade.action}
          </span>
          <span
            className={`text-xs font-mono px-2 py-0.5 rounded ${
              trade.outcome === "Yes"
                ? "bg-neon-cyan/20 text-neon-cyan"
                : "bg-neon-yellow/20 text-neon-yellow"
            }`}
          >
            {trade.outcome.toUpperCase()}
          </span>
        </div>
        <span className="text-gray-500 text-xs">{formatTimeAgo(trade.timestamp)}</span>
      </div>

      {/* Market Question */}
      <p className="text-white text-sm mb-3 line-clamp-2 group-hover:text-neon-magenta transition-colors">
        {trade.market_question}
      </p>

      {/* Trade Details */}
      <div className="flex items-center justify-between text-xs">
        <div className="flex items-center gap-4">
          <div>
            <span className="text-gray-500">Shares: </span>
            <span className="text-white font-mono">{trade.size.toLocaleString()}</span>
          </div>
          <div>
            <span className="text-gray-500">@ </span>
            <span className="text-neon-cyan font-mono">{(trade.price * 100).toFixed(1)}¢</span>
          </div>
        </div>
        <div className={`font-mono font-bold ${isBuy ? "text-neon-green" : "text-neon-red"}`}>
          {formatUSD(trade.usd_value)}
        </div>
      </div>
    </motion.a>
  );
}

export function WhaleTracker() {
  const { data, isLoading, error } = useQuery<WhaleActivity[]>({
    queryKey: ["whale-activity"],
    queryFn: () => fetchWhaleActivity(30),
    refetchInterval: 30000, // Refresh every 30 seconds
  });

  const trades = data || [];

  return (
    <GlowingBorder color="magenta" className="p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <NeonText color="magenta" size="lg">
            WHALE TRACKER
          </NeonText>
          {!isLoading && !error && trades.length > 0 && <PulsingDot color="magenta" size="sm" />}
        </div>
        <span className="text-gray-500 text-xs">
          {trades.length > 0 ? `${trades.length} large trades` : "Real trades from Polymarket"}
        </span>
      </div>

      {/* Trades List */}
      <AnimatePresence mode="wait">
        {isLoading ? (
          <motion.div
            key="loading"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="text-center py-12"
          >
            <motion.div
              animate={{ opacity: [0.5, 1, 0.5] }}
              transition={{ duration: 1.5, repeat: Infinity }}
              className="text-neon-magenta"
            >
              Loading whale activity...
            </motion.div>
          </motion.div>
        ) : error ? (
          <motion.div
            key="error"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="text-center py-12 text-gray-500"
          >
            <p>Failed to load whale activity.</p>
            <p className="text-xs mt-2">The Polymarket Data API may be temporarily unavailable.</p>
          </motion.div>
        ) : trades.length === 0 ? (
          <motion.div
            key="empty"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="text-center py-12 text-gray-500"
          >
            <p>No large trades found recently.</p>
            <p className="text-xs mt-2">Showing trades &gt;$1,000 USD</p>
          </motion.div>
        ) : (
          <motion.div
            key="results"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="space-y-3 max-h-[550px] overflow-y-auto pr-2"
          >
            {trades.map((trade, index) => (
              <TradeCard
                key={`${trade.transaction_hash || index}-${trade.timestamp}`}
                trade={trade}
                index={index}
              />
            ))}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Footer */}
      <div className="mt-4 pt-3 border-t border-dark-border">
        <p className="text-gray-500 text-xs">
          <span className="text-neon-magenta">REAL DATA:</span> Large trades (&gt;$1K) from
          Polymarket Data API. Click any trade to view the market.
        </p>
      </div>
    </GlowingBorder>
  );
}
