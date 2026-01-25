"use client";

import { useQuery } from "@tanstack/react-query";
import { motion, AnimatePresence } from "framer-motion";
import { GlowingBorder } from "../shared/GlowingBorder";
import { NeonText } from "../shared/NeonText";
import { fetchWhales, fetchWhaleActivity } from "@/lib/api";
import { Whale, WhaleActivity } from "@/types/whale";

function formatAddress(address: string): string {
  return `${address.slice(0, 6)}...${address.slice(-4)}`;
}

function formatCurrency(value: number): string {
  if (Math.abs(value) >= 1000000) {
    return `$${(value / 1000000).toFixed(1)}M`;
  }
  if (Math.abs(value) >= 1000) {
    return `$${(value / 1000).toFixed(1)}K`;
  }
  return `$${value.toFixed(0)}`;
}

function formatPercentage(value: number | null): string {
  if (value === null) return "N/A";
  return `${(value * 100).toFixed(1)}%`;
}

export function WhaleTracker() {
  const { data: whales, isLoading: whalesLoading } = useQuery({
    queryKey: ["whales"],
    queryFn: () => fetchWhales(10),
    refetchInterval: 30000,
  });

  const { data: activity, isLoading: activityLoading } = useQuery({
    queryKey: ["whale-activity"],
    queryFn: () => fetchWhaleActivity(10),
    refetchInterval: 15000,
  });

  return (
    <div className="space-y-6">
      {/* Top Whales Leaderboard */}
      <GlowingBorder color="magenta" className="p-6">
        <div className="flex items-center justify-between mb-4">
          <NeonText color="magenta" size="lg">
            TOP TRADERS
          </NeonText>
          <span className="text-gray-500 text-xs">Updated every 30s</span>
        </div>

        {whalesLoading ? (
          <div className="text-center py-8">
            <motion.div
              animate={{ opacity: [0.5, 1, 0.5] }}
              transition={{ duration: 1.5, repeat: Infinity }}
              className="text-neon-magenta"
            >
              Loading whale data...
            </motion.div>
          </div>
        ) : (
          <div className="space-y-2">
            {(whales as Whale[])?.slice(0, 5).map((whale, index) => (
              <motion.div
                key={whale.address}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.1 }}
                className="flex items-center justify-between p-3 bg-dark-surface rounded-lg border border-dark-border hover:border-neon-magenta/30 transition-colors"
              >
                <div className="flex items-center gap-3">
                  <span className="text-neon-magenta font-mono font-bold w-6">
                    #{index + 1}
                  </span>
                  <div>
                    <div className="font-mono text-sm text-white">
                      {whale.name || formatAddress(whale.address)}
                    </div>
                    <div className="text-xs text-gray-500">
                      {whale.positions_count} positions
                    </div>
                  </div>
                </div>
                <div className="text-right">
                  <div
                    className={`font-mono font-semibold ${
                      whale.profit_loss >= 0 ? "text-neon-green" : "text-neon-red"
                    }`}
                  >
                    {whale.profit_loss >= 0 ? "+" : ""}
                    {formatCurrency(whale.profit_loss)}
                  </div>
                  <div className="text-xs text-gray-500">
                    {formatPercentage(whale.win_rate)} win
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        )}
      </GlowingBorder>

      {/* Recent Whale Activity */}
      <GlowingBorder color="cyan" className="p-6">
        <div className="flex items-center justify-between mb-4">
          <NeonText color="cyan" size="lg">
            WHALE ACTIVITY
          </NeonText>
          <span className="text-gray-500 text-xs">Live feed</span>
        </div>

        {activityLoading ? (
          <div className="text-center py-8">
            <motion.div
              animate={{ opacity: [0.5, 1, 0.5] }}
              transition={{ duration: 1.5, repeat: Infinity }}
              className="text-neon-cyan"
            >
              Loading activity...
            </motion.div>
          </div>
        ) : (
          <div className="space-y-3 max-h-[400px] overflow-y-auto">
            <AnimatePresence>
              {(activity as WhaleActivity[])?.map((item, index) => (
                <motion.div
                  key={`${item.whale_address}-${item.timestamp}`}
                  initial={{ opacity: 0, y: -10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: 10 }}
                  transition={{ delay: index * 0.05 }}
                  className="p-3 bg-dark-surface rounded-lg border border-dark-border"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <span
                          className={`px-2 py-0.5 rounded text-xs font-bold ${
                            item.action === "BUY"
                              ? "bg-neon-green/20 text-neon-green"
                              : "bg-neon-red/20 text-neon-red"
                          }`}
                        >
                          {item.action}
                        </span>
                        <span
                          className={`px-2 py-0.5 rounded text-xs font-semibold ${
                            item.outcome === "Yes"
                              ? "bg-neon-cyan/20 text-neon-cyan"
                              : "bg-neon-magenta/20 text-neon-magenta"
                          }`}
                        >
                          {item.outcome}
                        </span>
                        <span className="text-gray-400 text-xs font-mono">
                          {item.whale_name || formatAddress(item.whale_address)}
                        </span>
                      </div>
                      <p className="text-sm text-gray-300 line-clamp-2">
                        {item.market_question}
                      </p>
                    </div>
                    <div className="text-right ml-4">
                      <div className="text-neon-yellow font-mono font-semibold">
                        {formatCurrency(item.usd_value)}
                      </div>
                      <div className="text-xs text-gray-500">
                        @ ${item.price.toFixed(2)}
                      </div>
                    </div>
                  </div>
                  <div className="text-xs text-gray-500 mt-2">
                    {new Date(item.timestamp).toLocaleTimeString()}
                  </div>
                </motion.div>
              ))}
            </AnimatePresence>
          </div>
        )}

        <div className="mt-4 pt-3 border-t border-dark-border">
          <p className="text-gray-500 text-xs">
            <span className="text-neon-cyan">TIP:</span> Follow whale trades to
            identify market sentiment shifts. Large buys often precede price
            movements.
          </p>
        </div>
      </GlowingBorder>
    </div>
  );
}
