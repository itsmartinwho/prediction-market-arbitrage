"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { motion, AnimatePresence } from "framer-motion";
import { GlowingBorder } from "../shared/GlowingBorder";
import { NeonText } from "../shared/NeonText";
import { fetchWhales, fetchWhaleActivity } from "@/lib/api";
import { Whale, WhaleActivity } from "@/types/whale";

type SubTab = "activity" | "traders";

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
  const [activeSubTab, setActiveSubTab] = useState<SubTab>("activity");

  const { data: whales, isLoading: whalesLoading } = useQuery({
    queryKey: ["whales"],
    queryFn: () => fetchWhales(15), // Increased from 10 to 15
    refetchInterval: 30000,
  });

  const { data: activity, isLoading: activityLoading } = useQuery({
    queryKey: ["whale-activity"],
    queryFn: () => fetchWhaleActivity(20), // Increased from 10 to 20
    refetchInterval: 15000,
  });

  const subTabs = [
    { id: "activity" as const, label: "ACTIVITY", color: "cyan" },
    { id: "traders" as const, label: "TOP TRADERS", color: "magenta" },
  ];

  return (
    <GlowingBorder color="magenta" className="p-6">
      {/* Header with Subtabs */}
      <div className="flex items-center justify-between mb-6">
        <NeonText color="magenta" size="lg">
          WHALE TRACKER
        </NeonText>

        {/* Subtab Navigation */}
        <div className="flex gap-1 bg-dark-surface rounded-lg p-1">
          {subTabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveSubTab(tab.id)}
              className={`px-4 py-1.5 rounded text-xs font-semibold transition-all duration-200 ${
                activeSubTab === tab.id
                  ? `bg-neon-${tab.color}/20 text-neon-${tab.color} border border-neon-${tab.color}/50`
                  : "text-gray-400 hover:text-gray-300"
              }`}
              style={
                activeSubTab === tab.id
                  ? {
                      backgroundColor:
                        tab.color === "cyan"
                          ? "rgba(0, 255, 255, 0.15)"
                          : "rgba(255, 0, 255, 0.15)",
                      borderColor:
                        tab.color === "cyan"
                          ? "rgba(0, 255, 255, 0.5)"
                          : "rgba(255, 0, 255, 0.5)",
                      color:
                        tab.color === "cyan"
                          ? "rgb(0, 255, 255)"
                          : "rgb(255, 0, 255)",
                    }
                  : {}
              }
            >
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* Content Area */}
      <AnimatePresence mode="wait">
        {activeSubTab === "activity" ? (
          <motion.div
            key="activity"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{ duration: 0.2 }}
          >
            <div className="flex items-center justify-between mb-3">
              <span className="text-gray-500 text-xs">Live feed • 20 recent trades</span>
              <span className="text-gray-500 text-xs">Updates every 15s</span>
            </div>

            {activityLoading ? (
              <div className="text-center py-12">
                <motion.div
                  animate={{ opacity: [0.5, 1, 0.5] }}
                  transition={{ duration: 1.5, repeat: Infinity }}
                  className="text-neon-cyan"
                >
                  Loading activity...
                </motion.div>
              </div>
            ) : (
              <div className="space-y-3 max-h-[600px] overflow-y-auto pr-2">
                <AnimatePresence>
                  {(activity as WhaleActivity[])?.map((item, index) => (
                    <motion.div
                      key={`${item.whale_address}-${item.timestamp}`}
                      initial={{ opacity: 0, y: -10 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: 10 }}
                      transition={{ delay: index * 0.03 }}
                      className="p-3 bg-dark-surface rounded-lg border border-dark-border hover:border-neon-cyan/30 transition-colors"
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
          </motion.div>
        ) : (
          <motion.div
            key="traders"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{ duration: 0.2 }}
          >
            <div className="flex items-center justify-between mb-3">
              <span className="text-gray-500 text-xs">Top 15 by profit/loss</span>
              <span className="text-gray-500 text-xs">Updates every 30s</span>
            </div>

            {whalesLoading ? (
              <div className="text-center py-12">
                <motion.div
                  animate={{ opacity: [0.5, 1, 0.5] }}
                  transition={{ duration: 1.5, repeat: Infinity }}
                  className="text-neon-magenta"
                >
                  Loading whale data...
                </motion.div>
              </div>
            ) : (
              <div className="space-y-2 max-h-[600px] overflow-y-auto pr-2">
                {(whales as Whale[])?.slice(0, 15).map((whale, index) => (
                  <motion.div
                    key={whale.address}
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: index * 0.05 }}
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
          </motion.div>
        )}
      </AnimatePresence>

      {/* Footer Tip */}
      <div className="mt-4 pt-3 border-t border-dark-border">
        <p className="text-gray-500 text-xs">
          <span className="text-neon-cyan">TIP:</span>{" "}
          {activeSubTab === "activity"
            ? "Follow whale trades to identify market sentiment shifts. Large buys often precede price movements."
            : "Top traders by realized P&L. Study their positions to understand winning strategies."}
        </p>
      </div>
    </GlowingBorder>
  );
}
