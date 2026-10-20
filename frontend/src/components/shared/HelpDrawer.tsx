"use client";

import { useEffect } from "react";
import { useStatus } from "@/hooks/useDashboard";

type TabType = "markets" | "whales" | "signals" | "explorer" | "arbitrage";

interface HelpDrawerProps {
  isOpen: boolean;
  onToggle: () => void;
  activeTab: TabType;
}

const HELP: Record<TabType, { title: string; items: [string, string][] }> = {
  markets: {
    title: "Markets",
    items: [
      ["Hot", "The events with the most trading in the last 24 hours."],
      ["Price movers", "Of those, the ones priced furthest from 50/50: strong consensus about the outcome."],
      ["Closing soon", "Events that end within 7 days, soonest first."],
      ["News", "A recent Google News headline for the event's title, when one arrives in time."],
    ],
  },
  whales: {
    title: "Whale trades",
    items: [
      ["What", "The largest of Polymarket's latest trades worth $1,000 or more, from its Data API."],
      ["Time", "When the trade happened, not when this page fetched it."],
      ["Who", "The trader's Polymarket pseudonym, or a shortened wallet address."],
    ],
  },
  signals: {
    title: "Signals",
    items: [
      ["Large trade", "A trade over $5,000. BUY or SELL repeats the trader's side; it is not advice."],
      ["Extreme price", "A market above 90% or below 10%. WATCH only."],
      ["High volume", "A market with over $100,000 traded. WATCH only."],
      ["Weight", "A heuristic for sorting, not a probability."],
    ],
  },
  explorer: {
    title: "Search",
    items: [
      ["Search", "Uses Polymarket's own search over open events."],
      ["Categories", "Each one searches a single representative word."],
    ],
  },
  arbitrage: {
    title: "Arbitrage",
    items: [
      ["Test", "Best YES ask + best NO ask under $1.00 after the assumed fee."],
      ["Prices", "From the CLOB order books. When one side has no asks, the price Gamma lists is used and counted."],
      ["Why it is usually empty", "Liquid markets are priced tightly, and edges close within seconds."],
    ],
  },
};

export function HelpDrawer({ isOpen, onToggle, activeTab }: HelpDrawerProps) {
  const status = useStatus().data;
  const help = HELP[activeTab];

  useEffect(() => {
    if (!isOpen) return;
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && onToggle();
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [isOpen, onToggle]);

  const settings: [string, string][] = status
    ? [
        [
          "Scanning",
          status.mode === "continuous"
            ? `Continuous, every ${status.scan_interval_seconds}s`
            : `On request, cached ${status.cache_ttl_seconds}s`,
        ],
        ["Markets per scan", `${status.market_limit} most liquid`],
        ["Edge threshold", `${(status.min_profit_threshold * 100).toFixed(1)}%`],
        ["Assumed fee", `$${status.fee.toFixed(2)} per $1 payout`],
        ["Alerts", status.alerts === "off" ? "Off (need the local loop)" : status.alerts === "telegram" ? "Telegram" : "Console"],
      ]
    : [];

  return (
    <>
      <button
        onClick={onToggle}
        aria-label={isOpen ? "Close help" : "Open help"}
        className="fixed bottom-6 right-6 z-40 flex h-11 w-11 items-center justify-center rounded-full border border-dark-border bg-dark-surface text-lg text-gray-300 shadow-lg transition-colors hover:border-gray-500 hover:text-white"
      >
        {isOpen ? "×" : "?"}
      </button>

      {isOpen && (
        <>
          <div onClick={onToggle} className="fixed inset-0 z-40 bg-black/50" aria-hidden />
          <aside
            role="dialog"
            aria-label="Help"
            className="fixed right-0 top-0 z-50 h-full w-full max-w-sm overflow-y-auto border-l border-dark-border bg-dark-gray p-6"
          >
            <div className="mb-6 flex items-center justify-between">
              <h2 className="text-lg font-semibold text-gray-100">{help.title}</h2>
              <button onClick={onToggle} className="text-2xl text-gray-400 hover:text-white" aria-label="Close help">
                ×
              </button>
            </div>

            <dl className="space-y-4 text-sm">
              {help.items.map(([term, text]) => (
                <div key={term}>
                  <dt className="mb-1 font-medium text-gray-200">{term}</dt>
                  <dd className="text-gray-400">{text}</dd>
                </div>
              ))}
            </dl>

            {settings.length > 0 && (
              <div className="mt-8 rounded-lg border border-dark-border bg-dark-surface p-4 text-sm">
                <h3 className="mb-3 font-medium text-gray-200">This deployment</h3>
                <dl className="space-y-2">
                  {settings.map(([term, value]) => (
                    <div key={term} className="flex justify-between gap-4">
                      <dt className="text-gray-500">{term}</dt>
                      <dd className="text-right font-mono text-xs text-gray-300">{value}</dd>
                    </div>
                  ))}
                </dl>
              </div>
            )}

            <p className="mt-6 text-xs text-gray-500">
              Research and paper trading only. It reads public data and cannot place a trade. Not financial advice.
            </p>
          </aside>
        </>
      )}
    </>
  );
}
