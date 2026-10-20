"use client";

import { useEffect, useState } from "react";
import { StatsStrip } from "@/components/dashboard/StatsStrip";
import { OpportunityFeed } from "@/components/dashboard/OpportunityFeed";
import { MarketActivity } from "@/components/dashboard/MarketActivity";
import { MarketExplorer } from "@/components/dashboard/MarketExplorer";
import { WhaleTracker } from "@/components/dashboard/WhaleTracker";
import { SignalsFeed } from "@/components/dashboard/SignalsFeed";
import { HelpDrawer } from "@/components/shared/HelpDrawer";

type TabType = "markets" | "whales" | "signals" | "explorer" | "arbitrage";

const tabs: { id: TabType; label: string }[] = [
  { id: "markets", label: "Markets" },
  { id: "whales", label: "Whale trades" },
  { id: "signals", label: "Signals" },
  { id: "explorer", label: "Search" },
  { id: "arbitrage", label: "Arbitrage" },
];

export default function Dashboard() {
  const [activeTab, setActiveTab] = useState<TabType>("markets");
  const [isHelpOpen, setIsHelpOpen] = useState(false);

  // Each tab has a link: /#whales, /#arbitrage, ...
  useEffect(() => {
    const fromHash = () => {
      const id = window.location.hash.slice(1) as TabType;
      if (tabs.some((t) => t.id === id)) setActiveTab(id);
    };
    fromHash();
    window.addEventListener("hashchange", fromHash);
    return () => window.removeEventListener("hashchange", fromHash);
  }, []);

  const selectTab = (id: TabType) => {
    setActiveTab(id);
    window.history.replaceState(null, "", id === "markets" ? window.location.pathname : `#${id}`);
  };

  return (
    <div className="mx-auto min-h-screen max-w-6xl px-4 py-6 sm:px-6">
      <header className="mb-6 flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div className="lg:flex-1">
          <h1 className="text-2xl font-semibold tracking-tight text-gray-100">
            Polymarket arbitrage scanner
          </h1>
          <p className="mt-1 text-sm text-gray-500">
            Live, read-only Polymarket data. Research, not financial advice. By{" "}
            <a
              href="https://github.com/itsmartinwho/"
              target="_blank"
              rel="noopener noreferrer"
              className="text-neon-cyan hover:underline"
            >
              JJ Martin
            </a>
            .
          </p>
        </div>
        <StatsStrip />
      </header>

      <nav className="mb-6 flex gap-1 overflow-x-auto border-b border-dark-border" aria-label="Sections">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => selectTab(tab.id)}
            aria-current={activeTab === tab.id ? "page" : undefined}
            className={`-mb-px whitespace-nowrap border-b-2 px-4 py-2.5 text-sm transition-colors ${
              activeTab === tab.id
                ? "border-neon-cyan text-gray-100"
                : "border-transparent text-gray-400 hover:text-gray-200"
            }`}
          >
            {tab.label}
          </button>
        ))}
      </nav>

      <main>
        {activeTab === "markets" && <MarketActivity />}
        {activeTab === "whales" && <WhaleTracker />}
        {activeTab === "signals" && <SignalsFeed />}
        {activeTab === "explorer" && <MarketExplorer />}
        {activeTab === "arbitrage" && <OpportunityFeed />}
      </main>

      <HelpDrawer isOpen={isHelpOpen} onToggle={() => setIsHelpOpen(!isHelpOpen)} activeTab={activeTab} />

      <footer className="mt-12 flex flex-col gap-2 border-t border-dark-border pt-6 text-xs text-gray-500 sm:flex-row sm:justify-between">
        <span>
          Data: Polymarket&apos;s Gamma, CLOB and Data APIs, and Google News. Nothing here can place a trade.
        </span>
        <a
          href="https://github.com/itsmartinwho/prediction-market-arbitrage"
          target="_blank"
          rel="noopener noreferrer"
          className="text-gray-400 hover:text-gray-200"
        >
          Source on GitHub
        </a>
      </footer>
    </div>
  );
}
