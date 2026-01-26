"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { motion, AnimatePresence } from "framer-motion";
import { GlowingBorder } from "../shared/GlowingBorder";
import { NeonText } from "../shared/NeonText";
import { fetchHotMarkets, fetchPriceMovers, fetchClosingSoon } from "@/lib/api";
import { MarketSummary, MarketListResponse } from "@/types/market";

type SubTab = "hot" | "movers" | "closing";

function formatVolume(value: number): string {
  if (value >= 1000000) {
    return `$${(value / 1000000).toFixed(1)}M`;
  }
  if (value >= 1000) {
    return `$${(value / 1000).toFixed(1)}K`;
  }
  return `$${value.toFixed(0)}`;
}

function formatPrice(price: number | null): string {
  if (price === null) return "N/A";
  return `${(price * 100).toFixed(0)}¢`;
}

function formatTimeRemaining(endDate: string | null): string {
  if (!endDate) return "No end date";

  const end = new Date(endDate);
  const now = new Date();
  const diffMs = end.getTime() - now.getTime();

  if (diffMs < 0) return "Ended";

  const days = Math.floor(diffMs / (1000 * 60 * 60 * 24));
  const hours = Math.floor((diffMs % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));

  if (days > 0) return `${days}d ${hours}h`;
  if (hours > 0) return `${hours}h`;

  const mins = Math.floor((diffMs % (1000 * 60 * 60)) / (1000 * 60));
  return `${mins}m`;
}

function MarketCard({ market, index }: { market: MarketSummary; index: number }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: -10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.03 }}
      className="p-4 bg-dark-surface rounded-lg border border-dark-border hover:border-neon-cyan/40 transition-all duration-200"
    >
      {/* Event Title */}
      <a
        href={market.polymarket_url}
        target="_blank"
        rel="noopener noreferrer"
        className="block"
      >
        <h3 className="text-sm font-medium text-white mb-3 line-clamp-2 hover:text-neon-cyan transition-colors">
          {market.title || (market as any).question || "Untitled Market"}
        </h3>
      </a>

      {/* Prices and Market Count */}
      <div className="flex items-center gap-4 mb-3">
        {market.market_count === 1 ? (
          <>
            <div className="flex items-center gap-2">
              <span className="text-xs text-gray-500">YES:</span>
              <span className="text-neon-green font-mono text-sm">
                {formatPrice(market.yes_price)}
              </span>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-xs text-gray-500">NO:</span>
              <span className="text-neon-red font-mono text-sm">
                {formatPrice(market.no_price)}
              </span>
            </div>
          </>
        ) : (
          <span className="text-xs text-neon-cyan">
            {market.market_count} outcomes
          </span>
        )}
      </div>

      {/* Volume and End Date */}
      <div className="flex items-center justify-between text-xs text-gray-500 mb-2">
        <span>Vol: {formatVolume(market.volume)}</span>
        {market.end_date && (
          <span className="text-neon-yellow">{formatTimeRemaining(market.end_date)}</span>
        )}
      </div>

      {/* Related News */}
      {market.news && (
        <a
          href={market.news.url}
          target="_blank"
          rel="noopener noreferrer"
          className="block mt-3 pt-3 border-t border-dark-border/50"
          onClick={(e) => e.stopPropagation()}
        >
          <div className="flex items-start gap-2">
            <span className="text-neon-orange text-xs shrink-0">NEWS</span>
            <p className="text-xs text-gray-400 line-clamp-2 hover:text-gray-300 transition-colors">
              {market.news.title}
            </p>
          </div>
          <span className="text-xs text-gray-600 mt-1 block">
            via {market.news.source}
          </span>
        </a>
      )}
    </motion.div>
  );
}

export function MarketActivity() {
  const [activeSubTab, setActiveSubTab] = useState<SubTab>("hot");

  const { data: hotData, isLoading: hotLoading } = useQuery<MarketListResponse>({
    queryKey: ["hot-markets"],
    queryFn: () => fetchHotMarkets(20),
    refetchInterval: 60000, // Every minute
  });

  const { data: moversData, isLoading: moversLoading } = useQuery<MarketListResponse>({
    queryKey: ["price-movers"],
    queryFn: () => fetchPriceMovers(20),
    refetchInterval: 60000,
  });

  const { data: closingData, isLoading: closingLoading } = useQuery<MarketListResponse>({
    queryKey: ["closing-soon"],
    queryFn: () => fetchClosingSoon(7, 20),
    refetchInterval: 60000,
  });

  const subTabs = [
    { id: "hot" as const, label: "HOT MARKETS", color: "cyan" },
    { id: "movers" as const, label: "PRICE MOVERS", color: "magenta" },
    { id: "closing" as const, label: "CLOSING SOON", color: "yellow" },
  ];

  const getActiveData = () => {
    switch (activeSubTab) {
      case "hot":
        return { data: hotData, loading: hotLoading };
      case "movers":
        return { data: moversData, loading: moversLoading };
      case "closing":
        return { data: closingData, loading: closingLoading };
    }
  };

  const { data, loading } = getActiveData();
  const markets = data?.markets || [];

  return (
    <GlowingBorder color="cyan" className="p-6">
      {/* Header with Subtabs */}
      <div className="flex items-center justify-between mb-6">
        <NeonText color="cyan" size="lg">
          MARKET ACTIVITY
        </NeonText>

        {/* Subtab Navigation */}
        <div className="flex gap-1 bg-dark-surface rounded-lg p-1">
          {subTabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveSubTab(tab.id)}
              className={`px-3 py-1.5 rounded text-xs font-semibold transition-all duration-200 ${
                activeSubTab === tab.id
                  ? "text-white"
                  : "text-gray-400 hover:text-gray-300"
              }`}
              style={
                activeSubTab === tab.id
                  ? {
                      backgroundColor:
                        tab.color === "cyan"
                          ? "rgba(0, 255, 255, 0.15)"
                          : tab.color === "magenta"
                          ? "rgba(255, 0, 255, 0.15)"
                          : "rgba(255, 255, 0, 0.15)",
                      borderWidth: "1px",
                      borderStyle: "solid",
                      borderColor:
                        tab.color === "cyan"
                          ? "rgba(0, 255, 255, 0.5)"
                          : tab.color === "magenta"
                          ? "rgba(255, 0, 255, 0.5)"
                          : "rgba(255, 255, 0, 0.5)",
                      color:
                        tab.color === "cyan"
                          ? "rgb(0, 255, 255)"
                          : tab.color === "magenta"
                          ? "rgb(255, 0, 255)"
                          : "rgb(255, 255, 0)",
                    }
                  : {}
              }
            >
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* Subtitle */}
      <div className="flex items-center justify-between mb-4">
        <span className="text-gray-500 text-xs">
          {activeSubTab === "hot" && "Highest trading volume"}
          {activeSubTab === "movers" && "Strong market conviction"}
          {activeSubTab === "closing" && "Ending within 7 days"}
        </span>
        <span className="text-gray-500 text-xs">
          {markets.length} markets • Click to trade
        </span>
      </div>

      {/* Content */}
      <AnimatePresence mode="wait">
        {loading ? (
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
              className="text-neon-cyan"
            >
              Loading markets...
            </motion.div>
          </motion.div>
        ) : markets.length === 0 ? (
          <motion.div
            key="empty"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="text-center py-12 text-gray-500"
          >
            No markets found
          </motion.div>
        ) : (
          <motion.div
            key={activeSubTab}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{ duration: 0.2 }}
            className="space-y-3 max-h-[600px] overflow-y-auto pr-2"
          >
            {markets.map((market, index) => (
              <MarketCard key={market.id} market={market} index={index} />
            ))}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Footer */}
      <div className="mt-4 pt-3 border-t border-dark-border">
        <p className="text-gray-500 text-xs">
          <span className="text-neon-cyan">TIP:</span>{" "}
          {activeSubTab === "hot" &&
            "High volume markets have better liquidity and tighter spreads."}
          {activeSubTab === "movers" &&
            "Markets with extreme prices show strong conviction - potential for mean reversion."}
          {activeSubTab === "closing" &&
            "Markets closing soon may have mispriced odds as resolution approaches."}
        </p>
      </div>
    </GlowingBorder>
  );
}
