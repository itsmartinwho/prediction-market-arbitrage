"use client";

import { motion, AnimatePresence } from "framer-motion";
import { GlowingBorder } from "./GlowingBorder";
import { NeonText } from "./NeonText";

type TabType = "whales" | "news" | "arbitrage";

interface HelpDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  activeTab: TabType;
}

export function HelpDrawer({ isOpen, onClose, activeTab }: HelpDrawerProps) {
  return (
    <>
      {/* Floating Help Button */}
      <button
        onClick={() => onClose()}
        className={`fixed bottom-6 right-6 z-40 w-12 h-12 rounded-full
          bg-dark-surface border-2 transition-all duration-300
          flex items-center justify-center text-xl font-bold
          ${
            isOpen
              ? "border-neon-magenta text-neon-magenta"
              : "border-neon-cyan/50 text-neon-cyan hover:border-neon-cyan"
          }`}
        style={{
          boxShadow: isOpen
            ? "0 0 20px rgba(255, 0, 255, 0.4)"
            : "0 0 10px rgba(0, 255, 255, 0.2)",
        }}
      >
        {isOpen ? "×" : "?"}
      </button>

      {/* Backdrop */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 bg-black/50 backdrop-blur-sm z-40"
          />
        )}
      </AnimatePresence>

      {/* Drawer Panel */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ x: "100%" }}
            animate={{ x: 0 }}
            exit={{ x: "100%" }}
            transition={{ type: "spring", damping: 30, stiffness: 300 }}
            className="fixed right-0 top-0 h-full w-96 bg-dark-gray/95
              backdrop-blur-lg border-l border-dark-border z-50
              overflow-y-auto p-6"
          >
            {/* Header */}
            <div className="flex items-center justify-between mb-6">
              <NeonText color="cyan" size="lg">
                HELP & INFO
              </NeonText>
              <button
                onClick={onClose}
                className="text-gray-400 hover:text-white text-2xl"
              >
                ×
              </button>
            </div>

            {/* Tab-Specific Content */}
            <div className="space-y-6">
              {activeTab === "whales" && <WhaleHelp />}
              {activeTab === "news" && <NewsHelp />}
              {activeTab === "arbitrage" && <ArbitrageHelp />}

              {/* Market Stats - Always visible */}
              <GlowingBorder className="p-4">
                <NeonText color="cyan" size="md" className="mb-3">
                  MARKET STATS
                </NeonText>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-400">Min Edge Threshold</span>
                    <span className="text-neon-green font-mono">1.0%</span>
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
                    <span className="text-neon-magenta font-mono">
                      DETECT ONLY
                    </span>
                  </div>
                </div>
              </GlowingBorder>

              {/* Disclaimer - Always visible */}
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
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}

function WhaleHelp() {
  return (
    <GlowingBorder color="magenta" className="p-4">
      <NeonText color="magenta" size="md" className="mb-3">
        WHALE TRACKING
      </NeonText>
      <div className="space-y-3 text-sm">
        <div>
          <div className="text-neon-magenta font-semibold mb-1">1. IDENTIFY</div>
          <p className="text-gray-400">
            Monitor top traders with the highest P&L and win rates on
            Polymarket.
          </p>
        </div>
        <div>
          <div className="text-neon-magenta font-semibold mb-1">2. TRACK</div>
          <p className="text-gray-400">
            Follow their positions and trades in real-time to spot market-moving
            activity.
          </p>
        </div>
        <div>
          <div className="text-neon-magenta font-semibold mb-1">3. MIRROR</div>
          <p className="text-gray-400">
            Consider following successful traders with proven track records.
          </p>
        </div>
      </div>
    </GlowingBorder>
  );
}

function NewsHelp() {
  return (
    <GlowingBorder color="yellow" className="p-4">
      <NeonText color="yellow" size="md" className="mb-3">
        NEWS SIGNALS
      </NeonText>
      <div className="space-y-3 text-sm">
        <div>
          <div className="text-neon-yellow font-semibold mb-1">1. AGGREGATE</div>
          <p className="text-gray-400">
            Collect breaking news from multiple sources related to prediction
            markets.
          </p>
        </div>
        <div>
          <div className="text-neon-yellow font-semibold mb-1">2. ANALYZE</div>
          <p className="text-gray-400">
            AI analyzes news sentiment and identifies affected markets before
            prices adjust.
          </p>
        </div>
        <div>
          <div className="text-neon-yellow font-semibold mb-1">3. SIGNAL</div>
          <p className="text-gray-400">
            Receive trading signals with confidence scores to act on news
            quickly.
          </p>
        </div>
      </div>
    </GlowingBorder>
  );
}

function ArbitrageHelp() {
  return (
    <GlowingBorder className="p-4">
      <NeonText color="cyan" size="md" className="mb-3">
        HOW ARBITRAGE WORKS
      </NeonText>
      <div className="space-y-3 text-sm">
        <div>
          <div className="text-neon-cyan font-semibold mb-1">1. DETECT</div>
          <p className="text-gray-400">
            Scanner monitors all Polymarket binary markets for YES + NO prices
            that sum to less than $1.00.
          </p>
        </div>
        <div>
          <div className="text-neon-cyan font-semibold mb-1">2. CALCULATE</div>
          <p className="text-gray-400">
            Profit = $1.00 payout - combined cost - 2% fee. Opportunities with
            &gt;1% edge are shown.
          </p>
        </div>
        <div>
          <div className="text-neon-cyan font-semibold mb-1">3. ALERT</div>
          <p className="text-gray-400">
            New opportunities trigger alerts for quick manual execution.
          </p>
        </div>
      </div>
    </GlowingBorder>
  );
}
