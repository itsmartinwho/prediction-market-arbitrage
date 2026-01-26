"use client";

import { useQuery } from "@tanstack/react-query";
import { motion, AnimatePresence } from "framer-motion";
import { GlowingBorder } from "../shared/GlowingBorder";
import { NeonText } from "../shared/NeonText";
import { PulsingDot } from "../shared/PulsingDot";
import { fetchNews } from "@/lib/api";
import { MarketSignal } from "@/types/news";

function getSignalColor(signal: string): string {
  if (signal.includes("BUY")) return "text-neon-green";
  if (signal.includes("SELL")) return "text-neon-red";
  return "text-neon-yellow";
}

function getSignalBgColor(signal: string): string {
  if (signal.includes("BUY")) return "bg-neon-green/10";
  if (signal.includes("SELL")) return "bg-neon-red/10";
  return "bg-neon-yellow/10";
}

function getTypeIcon(type: string): string {
  switch (type) {
    case "whale_trade":
      return "🐋";
    case "price_spike":
      return "📈";
    case "volume_surge":
      return "🔥";
    default:
      return "📊";
  }
}

function getTypeLabel(type: string): string {
  switch (type) {
    case "whale_trade":
      return "WHALE";
    case "price_spike":
      return "PRICE";
    case "volume_surge":
      return "VOLUME";
    default:
      return "SIGNAL";
  }
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
  return `${Math.floor(diffHours / 24)}d ago`;
}

function SignalCard({
  signal,
  index,
}: {
  signal: MarketSignal;
  index: number;
}) {
  const isActionable = signal.signal !== "WATCH";

  return (
    <motion.a
      href={signal.market_url}
      target="_blank"
      rel="noopener noreferrer"
      initial={{ opacity: 0, y: -10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.03 }}
      className="block p-4 bg-dark-surface rounded-lg border border-dark-border
                 hover:border-neon-orange/40 transition-all duration-200 group"
    >
      {/* Header: Type + Signal + Time */}
      <div className="flex items-start justify-between mb-2">
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-lg" title={signal.type}>
            {getTypeIcon(signal.type)}
          </span>
          <span className="text-xs text-gray-500 font-mono">
            {getTypeLabel(signal.type)}
          </span>
          <span
            className={`text-xs font-bold px-2 py-0.5 rounded ${getSignalColor(
              signal.signal
            )} ${getSignalBgColor(signal.signal)}`}
          >
            {signal.signal.replace("_", " ")}
          </span>
          <span className="text-xs text-gray-500">
            {(signal.confidence * 100).toFixed(0)}% conf
          </span>
        </div>
        <span className="text-xs text-gray-500">
          {formatTimeAgo(signal.detected_at)}
        </span>
      </div>

      {/* Title */}
      <h3 className="text-sm font-semibold text-neon-orange mb-1 group-hover:text-white transition-colors">
        {signal.title}
      </h3>

      {/* Market Question */}
      <p className="text-xs text-gray-400 mb-2 line-clamp-2">
        {signal.market_question}
      </p>

      {/* Summary */}
      <p className="text-xs text-gray-500 mb-2">{signal.summary}</p>

      {/* Reasoning */}
      <div className="text-xs text-gray-600 italic border-l-2 border-neon-orange/30 pl-2">
        {signal.reasoning}
      </div>

      {/* Current Price if available */}
      {signal.current_price !== null && (
        <div className="mt-2 text-xs">
          <span className="text-gray-500">Current: </span>
          <span className="text-neon-cyan font-mono">
            {(signal.current_price * 100).toFixed(1)}%
          </span>
        </div>
      )}
    </motion.a>
  );
}

export function SignalsFeed() {
  const {
    data: signals,
    isLoading,
    error,
  } = useQuery<MarketSignal[]>({
    queryKey: ["market-signals"],
    queryFn: () => fetchNews(20),
    refetchInterval: 30000, // Refresh every 30 seconds
  });

  const actionableSignals =
    signals?.filter((s) => s.signal !== "WATCH").length || 0;

  return (
    <GlowingBorder color="orange" className="p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <NeonText color="orange" size="lg">
            MARKET SIGNALS
          </NeonText>
          {actionableSignals > 0 && <PulsingDot color="orange" size="sm" />}
        </div>
        <span className="text-gray-500 text-xs">
          {actionableSignals > 0
            ? `${actionableSignals} actionable signal${
                actionableSignals !== 1 ? "s" : ""
              }`
            : "Monitoring market activity"}
        </span>
      </div>

      {/* Signals List */}
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
              className="text-neon-orange"
            >
              Analyzing market activity...
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
            <p>Failed to load market signals.</p>
            <p className="text-xs mt-2">Please try again later.</p>
          </motion.div>
        ) : (signals?.length || 0) === 0 ? (
          <motion.div
            key="empty"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="text-center py-12 text-gray-500"
          >
            <p>No signals detected.</p>
            <p className="text-xs mt-2">
              Watching for whale trades, price spikes, and volume surges.
            </p>
          </motion.div>
        ) : (
          <motion.div
            key="results"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="space-y-3 max-h-[550px] overflow-y-auto pr-2"
          >
            {signals?.map((signal, index) => (
              <SignalCard key={signal.id} signal={signal} index={index} />
            ))}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Footer */}
      <div className="mt-4 pt-3 border-t border-dark-border">
        <p className="text-gray-500 text-xs">
          <span className="text-neon-orange">REAL DATA:</span> Signals derived
          from live Polymarket trades and market activity. Click any signal to
          trade.
        </p>
      </div>
    </GlowingBorder>
  );
}
