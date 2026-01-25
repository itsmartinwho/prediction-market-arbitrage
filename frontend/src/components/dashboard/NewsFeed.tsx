"use client";

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
    return "bg-neon-green/20";
  }
  return "bg-neon-red/20";
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

export function NewsFeed() {
  const { data: news, isLoading: newsLoading } = useQuery({
    queryKey: ["news"],
    queryFn: () => fetchNews(10),
    refetchInterval: 60000,
  });

  const { data: signals, isLoading: signalsLoading } = useQuery({
    queryKey: ["news-signals"],
    queryFn: fetchNewsSignals,
    refetchInterval: 30000,
  });

  return (
    <div className="space-y-6">
      {/* Market Signals */}
      <GlowingBorder color="yellow" className="p-6">
        <div className="flex items-center justify-between mb-4">
          <NeonText color="yellow" size="lg">
            TRADING SIGNALS
          </NeonText>
          <span className="text-gray-500 text-xs">AI-Generated</span>
        </div>

        {signalsLoading ? (
          <div className="text-center py-8">
            <motion.div
              animate={{ opacity: [0.5, 1, 0.5] }}
              transition={{ duration: 1.5, repeat: Infinity }}
              className="text-neon-yellow"
            >
              Analyzing news for signals...
            </motion.div>
          </div>
        ) : (signals as MarketSignal[])?.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            No actionable signals at the moment
          </div>
        ) : (
          <div className="space-y-3">
            <AnimatePresence>
              {(signals as MarketSignal[])?.slice(0, 5).map((signal, index) => (
                <motion.div
                  key={`${signal.news_id}-${signal.market_id}`}
                  initial={{ opacity: 0, scale: 0.95 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.95 }}
                  transition={{ delay: index * 0.1 }}
                  className="p-4 bg-dark-surface rounded-lg border border-dark-border hover:border-neon-yellow/30 transition-colors"
                >
                  <div className="flex items-start justify-between mb-2">
                    <span
                      className={`px-3 py-1 rounded-full text-xs font-bold ${getSignalBg(
                        signal.signal
                      )} ${getSignalColor(signal.signal)}`}
                    >
                      {signal.signal.replace("_", " ")}
                    </span>
                    <div className="flex items-center gap-2">
                      <span className="text-xs text-gray-400">Confidence:</span>
                      <div className="w-16 h-2 bg-dark-border rounded-full overflow-hidden">
                        <div
                          className="h-full bg-neon-yellow rounded-full"
                          style={{ width: `${signal.confidence * 100}%` }}
                        />
                      </div>
                      <span className="text-xs text-neon-yellow font-mono">
                        {(signal.confidence * 100).toFixed(0)}%
                      </span>
                    </div>
                  </div>

                  <p className="text-sm text-white mb-2 line-clamp-2">
                    {signal.market_question}
                  </p>

                  <div className="flex items-center gap-4 text-xs">
                    {signal.current_price !== null && (
                      <span className="text-gray-400">
                        Current: <span className="text-neon-cyan font-mono">${signal.current_price.toFixed(2)}</span>
                      </span>
                    )}
                    {signal.target_price !== null && (
                      <span className="text-gray-400">
                        Target: <span className="text-neon-green font-mono">${signal.target_price.toFixed(2)}</span>
                      </span>
                    )}
                  </div>

                  <p className="text-xs text-gray-500 mt-2 italic">
                    {signal.reasoning}
                  </p>

                  <div className="text-xs text-gray-600 mt-2">
                    Based on: {signal.news_title}
                  </div>
                </motion.div>
              ))}
            </AnimatePresence>
          </div>
        )}
      </GlowingBorder>

      {/* News Feed */}
      <GlowingBorder color="cyan" className="p-6">
        <div className="flex items-center justify-between mb-4">
          <NeonText color="cyan" size="lg">
            NEWS FEED
          </NeonText>
          <span className="text-gray-500 text-xs">Market-moving news</span>
        </div>

        {newsLoading ? (
          <div className="text-center py-8">
            <motion.div
              animate={{ opacity: [0.5, 1, 0.5] }}
              transition={{ duration: 1.5, repeat: Infinity }}
              className="text-neon-cyan"
            >
              Loading news...
            </motion.div>
          </div>
        ) : (
          <div className="space-y-3 max-h-[500px] overflow-y-auto">
            <AnimatePresence>
              {(news as NewsItem[])?.map((item, index) => (
                <motion.a
                  key={item.id}
                  href={item.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  initial={{ opacity: 0, y: -10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: 10 }}
                  transition={{ delay: index * 0.05 }}
                  className="block p-4 bg-dark-surface rounded-lg border border-dark-border hover:border-neon-cyan/30 transition-colors cursor-pointer"
                >
                  <div className="flex items-start justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <span
                        className={`px-2 py-0.5 rounded text-xs font-semibold ${getSentimentBg(
                          item.sentiment
                        )} ${getSentimentColor(item.sentiment)}`}
                      >
                        {item.sentiment.toUpperCase()}
                      </span>
                      <span className="text-xs text-gray-500">{item.source}</span>
                    </div>
                    <span className="text-xs text-gray-500">
                      {formatTimeAgo(item.published_at)}
                    </span>
                  </div>

                  <h3 className="text-sm font-semibold text-white mb-2 hover:text-neon-cyan transition-colors">
                    {item.title}
                  </h3>

                  <p className="text-xs text-gray-400 line-clamp-2">
                    {item.summary}
                  </p>

                  {item.keywords.length > 0 && (
                    <div className="flex flex-wrap gap-1 mt-2">
                      {item.keywords.slice(0, 4).map((keyword) => (
                        <span
                          key={keyword}
                          className="px-2 py-0.5 bg-dark-border rounded text-xs text-gray-500"
                        >
                          {keyword}
                        </span>
                      ))}
                    </div>
                  )}

                  <div className="flex items-center gap-2 mt-2">
                    <span className="text-xs text-gray-500">Relevance:</span>
                    <div className="w-12 h-1.5 bg-dark-border rounded-full overflow-hidden">
                      <div
                        className="h-full bg-neon-cyan rounded-full"
                        style={{ width: `${item.relevance_score * 100}%` }}
                      />
                    </div>
                  </div>
                </motion.a>
              ))}
            </AnimatePresence>
          </div>
        )}

        <div className="mt-4 pt-3 border-t border-dark-border">
          <p className="text-gray-500 text-xs">
            <span className="text-neon-cyan">TIP:</span> News with high relevance
            scores are more likely to impact prediction market prices. Act fast
            on breaking news.
          </p>
        </div>
      </GlowingBorder>
    </div>
  );
}
