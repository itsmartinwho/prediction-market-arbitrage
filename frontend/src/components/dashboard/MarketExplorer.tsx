"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { motion, AnimatePresence } from "framer-motion";
import { GlowingBorder } from "../shared/GlowingBorder";
import { NeonText } from "../shared/NeonText";
import { searchMarkets, fetchHotMarkets } from "@/lib/api";
import { MarketSummary, MarketListResponse } from "@/types/market";

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
  if (!endDate) return "";

  const end = new Date(endDate);
  const now = new Date();
  const diffMs = end.getTime() - now.getTime();

  if (diffMs < 0) return "Ended";

  const days = Math.floor(diffMs / (1000 * 60 * 60 * 24));
  if (days > 30) return `${Math.floor(days / 30)}mo`;
  if (days > 0) return `${days}d`;

  const hours = Math.floor((diffMs % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
  return `${hours}h`;
}

const CATEGORIES = [
  { id: "all", label: "ALL" },
  { id: "politics", label: "POLITICS", keywords: ["trump", "biden", "election", "congress", "senate", "president"] },
  { id: "crypto", label: "CRYPTO", keywords: ["bitcoin", "btc", "ethereum", "eth", "crypto", "solana"] },
  { id: "sports", label: "SPORTS", keywords: ["nfl", "nba", "super bowl", "world cup", "championship"] },
  { id: "economy", label: "ECONOMY", keywords: ["fed", "rate", "inflation", "gdp", "recession"] },
];

function MarketCard({ market, index }: { market: MarketSummary; index: number }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: -10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.02 }}
      className="p-4 bg-dark-surface rounded-lg border border-dark-border hover:border-neon-yellow/40 transition-all duration-200"
    >
      {/* Event Title */}
      <a
        href={market.polymarket_url}
        target="_blank"
        rel="noopener noreferrer"
        className="block"
      >
        <h3 className="text-sm font-medium text-white mb-3 line-clamp-2 hover:text-neon-yellow transition-colors">
          {market.title}
        </h3>
      </a>

      {/* Prices and Volume */}
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-4">
          {market.market_count === 1 ? (
            <>
              <div className="flex items-center gap-1">
                <span className="text-xs text-gray-500">YES:</span>
                <span className="text-neon-green font-mono text-sm">
                  {formatPrice(market.yes_price)}
                </span>
              </div>
              <div className="flex items-center gap-1">
                <span className="text-xs text-gray-500">NO:</span>
                <span className="text-neon-red font-mono text-sm">
                  {formatPrice(market.no_price)}
                </span>
              </div>
            </>
          ) : (
            <span className="text-xs text-neon-yellow">
              {market.market_count} outcomes
            </span>
          )}
        </div>
        <div className="flex items-center gap-3 text-xs text-gray-500">
          <span>{formatVolume(market.volume)}</span>
          {market.end_date && (
            <span className="text-neon-cyan">{formatTimeRemaining(market.end_date)}</span>
          )}
        </div>
      </div>

      {/* Related News */}
      {market.news && (
        <a
          href={market.news.url}
          target="_blank"
          rel="noopener noreferrer"
          className="block mt-3 pt-3 border-t border-dark-border/50"
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

export function MarketExplorer() {
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedCategory, setSelectedCategory] = useState("all");
  const [debouncedQuery, setDebouncedQuery] = useState("");

  // Debounce search
  const handleSearchChange = (value: string) => {
    setSearchQuery(value);
    // Simple debounce
    setTimeout(() => {
      setDebouncedQuery(value);
    }, 300);
  };

  // Get category keywords for search
  const getCategorySearch = () => {
    if (selectedCategory === "all") return debouncedQuery;
    const category = CATEGORIES.find((c) => c.id === selectedCategory);
    if (!category || !("keywords" in category) || !category.keywords) return debouncedQuery;
    // If there's a search query, combine with category
    if (debouncedQuery) return debouncedQuery;
    // Otherwise use first category keyword
    return category.keywords[0];
  };

  const effectiveQuery = getCategorySearch();

  // Search or browse markets
  const { data, isLoading } = useQuery<MarketListResponse>({
    queryKey: ["market-explorer", effectiveQuery],
    queryFn: async () => {
      if (effectiveQuery && effectiveQuery.length > 0) {
        return searchMarkets(effectiveQuery, 30);
      }
      // Default to hot markets if no search
      return fetchHotMarkets(30);
    },
    refetchInterval: 60000,
  });

  const markets = data?.markets || [];

  return (
    <GlowingBorder color="yellow" className="p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <NeonText color="yellow" size="lg">
          MARKET EXPLORER
        </NeonText>
        <span className="text-gray-500 text-xs">
          Browse & search real Polymarket markets
        </span>
      </div>

      {/* Search Bar */}
      <div className="mb-4">
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => handleSearchChange(e.target.value)}
          placeholder="Search markets... (e.g., 'trump', 'bitcoin', 'super bowl')"
          className="w-full px-4 py-3 bg-dark-surface border border-dark-border rounded-lg
                     text-white placeholder-gray-500 text-sm
                     focus:outline-none focus:border-neon-yellow/50 transition-colors"
        />
      </div>

      {/* Category Filters */}
      <div className="flex flex-wrap gap-2 mb-6">
        {CATEGORIES.map((category) => (
          <button
            key={category.id}
            onClick={() => setSelectedCategory(category.id)}
            className={`px-3 py-1.5 rounded text-xs font-semibold transition-all duration-200 ${
              selectedCategory === category.id
                ? "bg-neon-yellow/20 text-neon-yellow border border-neon-yellow/50"
                : "bg-dark-surface text-gray-400 border border-dark-border hover:border-gray-500"
            }`}
          >
            {category.label}
          </button>
        ))}
      </div>

      {/* Results Count */}
      <div className="flex items-center justify-between mb-4">
        <span className="text-gray-500 text-xs">
          {effectiveQuery ? `Searching for "${effectiveQuery}"` : "Showing hot markets"}
        </span>
        <span className="text-gray-500 text-xs">
          {markets.length} results • Click to trade on Polymarket
        </span>
      </div>

      {/* Markets List */}
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
              className="text-neon-yellow"
            >
              Searching markets...
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
            No markets found for "{effectiveQuery}"
          </motion.div>
        ) : (
          <motion.div
            key="results"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="space-y-2 max-h-[550px] overflow-y-auto pr-2"
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
          <span className="text-neon-yellow">TIP:</span> All data comes directly
          from Polymarket. Click any market to view details and trade on Polymarket.
        </p>
      </div>
    </GlowingBorder>
  );
}
