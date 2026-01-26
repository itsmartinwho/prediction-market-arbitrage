"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { useOpportunitiesWebSocket } from "@/hooks/useWebSocket";
import { fetchScannerStats, triggerScan } from "@/lib/api";
import { StatsStrip } from "@/components/dashboard/StatsStrip";
import { OpportunityFeed } from "@/components/dashboard/OpportunityFeed";
import { MarketActivity } from "@/components/dashboard/MarketActivity";
import { MarketExplorer } from "@/components/dashboard/MarketExplorer";
import { WhaleTracker } from "@/components/dashboard/WhaleTracker";
import { NeonText } from "@/components/shared/NeonText";
import { GlowingBorder } from "@/components/shared/GlowingBorder";
import { HelpDrawer } from "@/components/shared/HelpDrawer";

type TabType = "markets" | "whales" | "explorer" | "arbitrage";

export default function Dashboard() {
  const [activeTab, setActiveTab] = useState<TabType>("markets");
  const [isHelpOpen, setIsHelpOpen] = useState(false);

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
    { id: "markets" as const, label: "MARKETS", color: "cyan" },
    { id: "whales" as const, label: "WHALE TRADES", color: "magenta" },
    { id: "explorer" as const, label: "SEARCH", color: "yellow" },
    { id: "arbitrage" as const, label: "ARBITRAGE", color: "green" },
  ];

  return (
    <div className="min-h-screen p-6">
      {/* Header */}
      <header className="mb-6">
        <div className="flex items-center justify-between">
          <div>
            <motion.h1
              className="text-3xl font-bold mb-1"
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
            >
              <NeonText color="cyan" size="2xl">
                POLYMARKET DASHBOARD
              </NeonText>
            </motion.h1>
            <p className="text-gray-500 text-sm">
              Real-time Polymarket data and arbitrage detection. By{" "}
              <a
                href="https://github.com/itsmartinwho/"
                target="_blank"
                rel="noopener noreferrer"
                className="text-neon-cyan hover:underline"
              >
                JJ Martin
              </a>
            </p>
          </div>

          <div className="flex items-center gap-4">
            {/* Compact Stats Strip */}
            <StatsStrip
              stats={stats || null}
              opportunityCount={opportunities.length}
              isConnected={isConnected}
            />

            <button
              onClick={handleManualScan}
              className="cyber-button"
            >
              SCAN
            </button>
            <GlowingBorder className="px-3 py-1.5">
              <span className="text-gray-400 text-xs">v0.2.0</span>
            </GlowingBorder>
          </div>
        </div>
      </header>

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
                        : tab.color === "green"
                        ? "rgba(0, 255, 0, 0.3)"
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

      {/* Main Content - Full Width */}
      <main>
        <motion.div
          key={activeTab}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
        >
          {activeTab === "markets" && <MarketActivity />}
          {activeTab === "whales" && <WhaleTracker />}
          {activeTab === "explorer" && <MarketExplorer />}
          {activeTab === "arbitrage" && (
            <OpportunityFeed
              opportunities={opportunities}
              isConnected={isConnected}
              lastUpdate={lastUpdate}
            />
          )}
        </motion.div>
      </main>

      {/* Help Drawer */}
      <HelpDrawer
        isOpen={isHelpOpen}
        onClose={() => setIsHelpOpen(!isHelpOpen)}
        activeTab={activeTab}
      />

      {/* Footer */}
      <footer className="mt-12 pt-6 border-t border-dark-border">
        <div className="flex items-center justify-between text-gray-500 text-xs">
          <div>
            Built by{" "}
            <a
              href="https://github.com/itsmartinwho/"
              target="_blank"
              rel="noopener noreferrer"
              className="text-neon-cyan hover:underline"
            >
              JJ Martin
            </a>
            {" "}| Real Polymarket Data
          </div>
          <div className="flex items-center gap-4">
            <span>Polymarket Gamma API</span>
            <span>|</span>
            <span>WebSocket Real-time</span>
            <span>|</span>
            <span>Live Market Data</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
