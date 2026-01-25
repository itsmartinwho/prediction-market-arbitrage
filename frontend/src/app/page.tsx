"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { useOpportunitiesWebSocket } from "@/hooks/useWebSocket";
import { fetchScannerStats, triggerScan } from "@/lib/api";
import { StatsCards } from "@/components/dashboard/StatsCards";
import { OpportunityFeed } from "@/components/dashboard/OpportunityFeed";
import { WhaleTracker } from "@/components/dashboard/WhaleTracker";
import { NewsFeed } from "@/components/dashboard/NewsFeed";
import { NeonText } from "@/components/shared/NeonText";
import { GlowingBorder } from "@/components/shared/GlowingBorder";

type TabType = "arbitrage" | "whales" | "news";

export default function Dashboard() {
  const [activeTab, setActiveTab] = useState<TabType>("arbitrage");

  // Real-time opportunities via WebSocket
  const { opportunities, isConnected, lastUpdate } = useOpportunitiesWebSocket();

  // Scanner stats via polling
  const { data: stats } = useQuery({
    queryKey: ["scanner-stats"],
    queryFn: fetchScannerStats,
    refetchInterval: 5000,
  });

  const handleManualScan = async () => {
    try {
      await triggerScan();
    } catch (error) {
      console.error("Failed to trigger scan:", error);
    }
  };

  const tabs = [
    { id: "arbitrage" as const, label: "ARBITRAGE", color: "cyan" },
    { id: "whales" as const, label: "WHALE TRACKER", color: "magenta" },
    { id: "news" as const, label: "NEWS FRONT-RUNNER", color: "yellow" },
  ];

  return (
    <div className="min-h-screen p-6">
      {/* Header */}
      <header className="mb-8">
        <div className="flex items-center justify-between">
          <div>
            <motion.h1
              className="text-3xl font-bold mb-2"
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
            >
              <NeonText color="cyan" size="2xl">
                POLYMARKET ARBITRAGE
              </NeonText>
            </motion.h1>
            <p className="text-gray-500 text-sm">
              Real-time arbitrage detection for prediction markets
            </p>
          </div>

          <div className="flex items-center gap-4">
            <button
              onClick={handleManualScan}
              className="cyber-button"
            >
              MANUAL SCAN
            </button>
            <GlowingBorder className="px-4 py-2">
              <span className="text-gray-400 text-sm">
                v0.1.0 | Detection Mode
              </span>
            </GlowingBorder>
          </div>
        </div>
      </header>

      {/* Stats Cards */}
      <section className="mb-8">
        <StatsCards
          stats={stats || null}
          opportunityCount={opportunities.length}
          isConnected={isConnected}
        />
      </section>

      {/* Tab Navigation */}
      <div className="flex gap-2 mb-6">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`px-6 py-3 rounded-lg font-semibold text-sm transition-all duration-300 ${
              activeTab === tab.id
                ? `bg-neon-${tab.color}/20 border-2 border-neon-${tab.color} text-neon-${tab.color} shadow-lg shadow-neon-${tab.color}/20`
                : "bg-dark-surface border border-dark-border text-gray-400 hover:border-gray-500"
            }`}
            style={
              activeTab === tab.id
                ? {
                    boxShadow: `0 0 20px ${
                      tab.color === "cyan"
                        ? "rgba(0, 255, 255, 0.3)"
                        : tab.color === "magenta"
                        ? "rgba(255, 0, 255, 0.3)"
                        : "rgba(255, 255, 0, 0.3)"
                    }`,
                  }
                : {}
            }
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Main Content */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Column */}
        <div className="lg:col-span-2">
          <motion.div
            key={activeTab}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3 }}
          >
            {activeTab === "arbitrage" && (
              <OpportunityFeed
                opportunities={opportunities}
                isConnected={isConnected}
                lastUpdate={lastUpdate}
              />
            )}
            {activeTab === "whales" && <WhaleTracker />}
            {activeTab === "news" && <NewsFeed />}
          </motion.div>
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Dynamic Info based on active tab */}
          {activeTab === "arbitrage" && (
            <>
              <GlowingBorder className="p-6">
                <NeonText color="magenta" size="lg" className="mb-4">
                  HOW IT WORKS
                </NeonText>
                <div className="space-y-4 text-sm">
                  <div>
                    <div className="text-neon-cyan font-semibold mb-1">
                      1. DETECT
                    </div>
                    <p className="text-gray-400">
                      Scanner monitors all Polymarket binary markets for YES + NO
                      prices that sum to less than $1.00.
                    </p>
                  </div>
                  <div>
                    <div className="text-neon-cyan font-semibold mb-1">
                      2. CALCULATE
                    </div>
                    <p className="text-gray-400">
                      Profit = $1.00 payout - combined cost - 2% fee.
                      Opportunities with &gt;2.5% edge are shown.
                    </p>
                  </div>
                  <div>
                    <div className="text-neon-cyan font-semibold mb-1">
                      3. ALERT
                    </div>
                    <p className="text-gray-400">
                      New opportunities trigger Telegram alerts for quick manual
                      execution.
                    </p>
                  </div>
                </div>
              </GlowingBorder>

              <GlowingBorder className="p-6">
                <NeonText color="cyan" size="lg" className="mb-4">
                  MARKET STATS
                </NeonText>
                <div className="space-y-3">
                  <div className="flex justify-between">
                    <span className="text-gray-400">Min Edge Threshold</span>
                    <span className="text-neon-green font-mono">2.5%</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-400">Polymarket Fee</span>
                    <span className="text-neon-yellow font-mono">2.0%</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-400">Scan Interval</span>
                    <span className="text-neon-cyan font-mono">5s</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-400">Mode</span>
                    <span className="text-neon-magenta font-mono">DETECT ONLY</span>
                  </div>
                </div>
              </GlowingBorder>
            </>
          )}

          {activeTab === "whales" && (
            <GlowingBorder color="magenta" className="p-6">
              <NeonText color="magenta" size="lg" className="mb-4">
                WHALE TRACKING
              </NeonText>
              <div className="space-y-4 text-sm">
                <div>
                  <div className="text-neon-magenta font-semibold mb-1">
                    1. IDENTIFY
                  </div>
                  <p className="text-gray-400">
                    Monitor top traders with the highest P&L and win rates on
                    Polymarket.
                  </p>
                </div>
                <div>
                  <div className="text-neon-magenta font-semibold mb-1">
                    2. TRACK
                  </div>
                  <p className="text-gray-400">
                    Follow their positions and trades in real-time to spot
                    market-moving activity.
                  </p>
                </div>
                <div>
                  <div className="text-neon-magenta font-semibold mb-1">
                    3. MIRROR
                  </div>
                  <p className="text-gray-400">
                    Consider following successful traders with proven track
                    records.
                  </p>
                </div>
              </div>
            </GlowingBorder>
          )}

          {activeTab === "news" && (
            <GlowingBorder color="yellow" className="p-6">
              <NeonText color="yellow" size="lg" className="mb-4">
                NEWS FRONT-RUNNING
              </NeonText>
              <div className="space-y-4 text-sm">
                <div>
                  <div className="text-neon-yellow font-semibold mb-1">
                    1. AGGREGATE
                  </div>
                  <p className="text-gray-400">
                    Collect breaking news from multiple sources related to
                    prediction markets.
                  </p>
                </div>
                <div>
                  <div className="text-neon-yellow font-semibold mb-1">
                    2. ANALYZE
                  </div>
                  <p className="text-gray-400">
                    AI analyzes news sentiment and identifies affected markets
                    before prices adjust.
                  </p>
                </div>
                <div>
                  <div className="text-neon-yellow font-semibold mb-1">
                    3. SIGNAL
                  </div>
                  <p className="text-gray-400">
                    Receive trading signals with confidence scores to act on
                    news quickly.
                  </p>
                </div>
              </div>
            </GlowingBorder>
          )}

          {/* Disclaimer - always visible */}
          <GlowingBorder color="red" className="p-4">
            <div className="text-neon-red text-xs font-semibold mb-2">
              DISCLAIMER
            </div>
            <p className="text-gray-500 text-xs">
              This tool is for educational purposes. Arbitrage opportunities
              may disappear quickly. Always verify prices before trading.
              Not financial advice.
            </p>
          </GlowingBorder>
        </div>
      </div>

      {/* Footer */}
      <footer className="mt-12 pt-6 border-t border-dark-border">
        <div className="flex items-center justify-between text-gray-500 text-xs">
          <div>
            Built for prediction market arbitrage detection
          </div>
          <div className="flex items-center gap-4">
            <span>Polymarket API</span>
            <span>|</span>
            <span>WebSocket Real-time</span>
            <span>|</span>
            <span>Telegram Alerts</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
