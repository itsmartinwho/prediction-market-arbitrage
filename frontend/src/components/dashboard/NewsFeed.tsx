"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { motion, AnimatePresence } from "framer-motion";
import { GlowingBorder } from "../shared/GlowingBorder";
import { NeonText } from "../shared/NeonText";
import { fetchNews, fetchNewsSignals } from "@/lib/api";
import { NewsItem, MarketSignal } from "@/types/news";

function getSentimentColor(sentiment: string): string {
  switch (sentiment) {
    case "bullish":
      return "text-neon-green";
    case "bearish":
      return "text-neon-red";
    default:
      return "text-gray-400";
  }
}

function getSentimentBg(sentiment: string): string {
  switch (sentiment) {
    case "bullish":
      return "bg-neon-green/20";
    case "bearish":
      return "bg-neon-red/20";
    default:
      return "bg-gray-500/20";
  }
}

function getSignalColor(signal: string): string {
  if (signal.includes("BUY")) {
    return "text-neon-green";
  }
  return "text-neon-red";
}

function getSignalBg(signal: string): string {
  if (signal.includes("BUY")) {
    return "bg-neon-green/20 border-neon-green/50";
  }
  return "bg-neon-red/20 border-neon-red/50";
}

function formatTimeAgo(dateString: string): string {
  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);

  if (diffMins < 1) return "Just now";
  if (diffMins < 60) return `${diffMins}m ago`;

  const diffHours = Math.floor(diffMins / 60);
  if (diffHours < 24) return `${diffHours}h ago`;

  const diffDays = Math.floor(diffHours / 24);
  return `${diffDays}d ago`;
}

function formatSignal(signal: string): string {
  return signal.replace("_", " ");
}

interface NewsWithSignal extends NewsItem {
  signal?: MarketSignal;
}

export function NewsFeed() {
  const [expandedNews, setExpandedNews] = useState<string | null>(null);

  const { data: news, isLoading: newsLoading } = useQuery({
    queryKey: ["news"],
    queryFn: () => fetchNews(15), // Increased to 15
    refetchInterval: 60000,
  });

  const { data: signals, isLoading: signalsLoading } = useQuery({
    queryKey: ["news-signals"],
    queryFn: fetchNewsSignals,
    refetchInterval: 30000,
  });

  // Merge news with their signals and sort (news with signals first)
  const mergedNews: NewsWithSignal[] = (news as NewsItem[] || []).map((item) => {
    const matchingSignal = (signals as MarketSignal[] || []).find(
      (s) => s.news_id === item.id
    );
    return {
      ...item,
      signal: matchingSignal,
    };
  }).sort((a, b) => {
    // News with signals first, then by published date
    if (a.signal && !b.signal) return -1;
    if (!a.signal && b.signal) return 1;
    // If both have signals, higher confidence first
    if (a.signal && b.signal) {
      return b.signal.confidence - a.signal.confidence;
    }
    return new Date(b.published_at).getTime() - new Date(a.published_at).getTime();
  });

  const isLoading = newsLoading || signalsLoading;
  const signalCount = mergedNews.filter((n) => n.signal).length;

  const toggleExpand = (id: string) => {
    setExpandedNews(expandedNews === id ? null : id);
  };

  return (
    <GlowingBorder color="yellow" className="p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-4">
          <NeonText color="yellow" size="lg">
            NEWS SIGNALS
          </NeonText>
          {signalCount > 0 && (
            <span className="px-2 py-0.5 rounded-full text-xs font-bold bg-neon-yellow/20 text-neon-yellow border border-neon-yellow/50">
              {signalCount} ACTIVE SIGNAL{signalCount !== 1 ? "S" : ""}
            </span>
          )}
        </div>
        <span className="text-gray-500 text-xs">
          News with trading signals highlighted
        </span>
      </div>

      {isLoading ? (
        <div className="text-center py-12">
          <motion.div
            animate={{ opacity: [0.5, 1, 0.5] }}
            transition={{ duration: 1.5, repeat: Infinity }}
            className="text-neon-yellow"
          >
            Loading news and analyzing signals...
          </motion.div>
        </div>
      ) : mergedNews.length === 0 ? (
        <div className="text-center py-12 text-gray-500">
          No news available at the moment
        </div>
      ) : (
        <div className="space-y-3 max-h-[650px] overflow-y-auto pr-2">
          <AnimatePresence>
            {mergedNews.map((item, index) => (
              <motion.div
                key={item.id}
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: 10 }}
                transition={{ delay: index * 0.03 }}
                className={`p-4 bg-dark-surface rounded-lg border transition-all duration-200 cursor-pointer ${
                  item.signal
                    ? "border-neon-yellow/40 hover:border-neon-yellow/70"
                    : "border-dark-border hover:border-gray-600"
                }`}
                onClick={() => toggleExpand(item.id)}
              >
                {/* News Header */}
                <div className="flex items-start justify-between mb-2">
                  <div className="flex items-center gap-2 flex-wrap">
                    {/* Signal Badge (if exists) */}
                    {item.signal && (
                      <span
                        className={`px-2 py-0.5 rounded text-xs font-bold border ${getSignalBg(
                          item.signal.signal
                        )} ${getSignalColor(item.signal.signal)}`}
                      >
                        {formatSignal(item.signal.signal)}{" "}
                        {(item.signal.confidence * 100).toFixed(0)}%
                      </span>
                    )}
                    {/* Sentiment Badge */}
                    <span
                      className={`px-2 py-0.5 rounded text-xs font-semibold ${getSentimentBg(
                        item.sentiment
                      )} ${getSentimentColor(item.sentiment)}`}
                    >
                      {item.sentiment.toUpperCase()}
                    </span>
                    <span className="text-xs text-gray-500">{item.source}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-gray-500">
                      {formatTimeAgo(item.published_at)}
                    </span>
                    <span className="text-gray-600 text-xs">
                      {expandedNews === item.id ? "▲" : "▼"}
                    </span>
                  </div>
                </div>

                {/* News Title */}
                <a
                  href={item.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  onClick={(e) => e.stopPropagation()}
                  className="block"
                >
                  <h3 className="text-sm font-semibold text-white mb-2 hover:text-neon-cyan transition-colors">
                    {item.title}
                  </h3>
                </a>

                {/* Summary (always visible) */}
                <p className="text-xs text-gray-400 line-clamp-2">
                  {item.summary}
                </p>

                {/* Expanded Signal Details */}
                <AnimatePresence>
                  {expandedNews === item.id && item.signal && (
                    <motion.div
                      initial={{ height: 0, opacity: 0 }}
                      animate={{ height: "auto", opacity: 1 }}
                      exit={{ height: 0, opacity: 0 }}
                      transition={{ duration: 0.2 }}
                      className="overflow-hidden"
                    >
                      <div className="mt-4 pt-4 border-t border-dark-border">
                        {/* Signal Details */}
                        <div className="flex items-center justify-between mb-3">
                          <span className="text-xs text-gray-400">
                            Signal Details
                          </span>
                          <div className="flex items-center gap-2">
                            <span className="text-xs text-gray-400">
                              Confidence:
                            </span>
                            <div className="w-16 h-2 bg-dark-border rounded-full overflow-hidden">
                              <div
                                className="h-full bg-neon-yellow rounded-full"
                                style={{
                                  width: `${item.signal.confidence * 100}%`,
                                }}
                              />
                            </div>
                            <span className="text-xs text-neon-yellow font-mono">
                              {(item.signal.confidence * 100).toFixed(0)}%
                            </span>
                          </div>
                        </div>

                        {/* Market Question */}
                        <p className="text-sm text-white mb-3">
                          {item.signal.market_question}
                        </p>

                        {/* Prices */}
                        <div className="flex items-center gap-6 mb-3">
                          {item.signal.current_price !== null && (
                            <div className="text-xs">
                              <span className="text-gray-400">Current: </span>
                              <span className="text-neon-cyan font-mono font-semibold">
                                ${item.signal.current_price.toFixed(2)}
                              </span>
                            </div>
                          )}
                          {item.signal.target_price !== null && (
                            <div className="text-xs">
                              <span className="text-gray-400">Target: </span>
                              <span className="text-neon-green font-mono font-semibold">
                                ${item.signal.target_price.toFixed(2)}
                              </span>
                            </div>
                          )}
                          {item.signal.current_price !== null &&
                            item.signal.target_price !== null && (
                              <div className="text-xs">
                                <span className="text-gray-400">Upside: </span>
                                <span className="text-neon-yellow font-mono font-semibold">
                                  +
                                  {(
                                    ((item.signal.target_price -
                                      item.signal.current_price) /
                                      item.signal.current_price) *
                                    100
                                  ).toFixed(1)}
                                  %
                                </span>
                              </div>
                            )}
                        </div>

                        {/* Reasoning */}
                        <p className="text-xs text-gray-500 italic mb-4">
                          {item.signal.reasoning}
                        </p>

                        {/* Trade Button (only for high confidence) */}
                        {item.signal.confidence >= 0.7 && (
                          <a
                            href={`https://polymarket.com/event/${item.signal.market_id}`}
                            target="_blank"
                            rel="noopener noreferrer"
                            onClick={(e) => e.stopPropagation()}
                            className="inline-flex items-center gap-2 px-4 py-2 bg-neon-yellow/20 border border-neon-yellow/50 text-neon-yellow rounded hover:bg-neon-yellow/30 transition-colors text-xs font-semibold"
                          >
                            TRADE ON POLYMARKET →
                          </a>
                        )}
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>

                {/* Expanded News Details (without signal) */}
                <AnimatePresence>
                  {expandedNews === item.id && !item.signal && (
                    <motion.div
                      initial={{ height: 0, opacity: 0 }}
                      animate={{ height: "auto", opacity: 1 }}
                      exit={{ height: 0, opacity: 0 }}
                      transition={{ duration: 0.2 }}
                      className="overflow-hidden"
                    >
                      <div className="mt-4 pt-4 border-t border-dark-border">
                        {/* Keywords */}
                        {item.keywords.length > 0 && (
                          <div className="flex flex-wrap gap-1 mb-3">
                            {item.keywords.slice(0, 6).map((keyword) => (
                              <span
                                key={keyword}
                                className="px-2 py-0.5 bg-dark-border rounded text-xs text-gray-500"
                              >
                                {keyword}
                              </span>
                            ))}
                          </div>
                        )}

                        {/* Relevance */}
                        <div className="flex items-center gap-2">
                          <span className="text-xs text-gray-500">
                            Relevance:
                          </span>
                          <div className="w-16 h-1.5 bg-dark-border rounded-full overflow-hidden">
                            <div
                              className="h-full bg-neon-cyan rounded-full"
                              style={{ width: `${item.relevance_score * 100}%` }}
                            />
                          </div>
                          <span className="text-xs text-gray-500">
                            {(item.relevance_score * 100).toFixed(0)}%
                          </span>
                        </div>

                        <p className="text-xs text-gray-600 mt-3">
                          No trading signal generated for this news item.
                        </p>
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </motion.div>
            ))}
          </AnimatePresence>
        </div>
      )}

      {/* Footer Tip */}
      <div className="mt-4 pt-3 border-t border-dark-border">
        <p className="text-gray-500 text-xs">
          <span className="text-neon-yellow">TIP:</span> News items with trading
          signals are shown first. Click to expand and see signal details.
          High-confidence signals (&gt;70%) include direct trade links.
        </p>
      </div>
    </GlowingBorder>
  );
}
