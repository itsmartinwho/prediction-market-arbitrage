"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { GlowingBorder } from "../shared/GlowingBorder";
import { NeonText } from "../shared/NeonText";
import { EmptyState, ErrorState, LoadingState, StaleNotice } from "../shared/QueryState";
import { MarketCard } from "./MarketCard";
import { fetchClosingSoon, fetchHotMarkets, fetchPriceMovers } from "@/lib/api";
import { timeAgo } from "@/lib/format";
import { useNow } from "@/hooks/useNow";
import { MarketListResponse } from "@/types/market";

type SubTab = "hot" | "movers" | "closing";

const subTabs: { id: SubTab; label: string; blurb: string; tip: string }[] = [
  {
    id: "hot",
    label: "Hot",
    blurb: "Most traded in the last 24 hours",
    tip: "High-volume markets have more liquidity and tighter spreads.",
  },
  {
    id: "movers",
    label: "Price movers",
    blurb: "Of the hot markets, those priced furthest from 50/50",
    tip: "An extreme price is strong consensus, not certainty.",
  },
  {
    id: "closing",
    label: "Closing soon",
    blurb: "Ending within 7 days, soonest first",
    tip: "Prices tend to converge on the outcome as resolution nears.",
  },
];

const fetchers: Record<SubTab, () => Promise<MarketListResponse>> = {
  hot: () => fetchHotMarkets(20),
  movers: () => fetchPriceMovers(20),
  closing: () => fetchClosingSoon(7, 20),
};

export function MarketActivity() {
  const [activeSubTab, setActiveSubTab] = useState<SubTab>("hot");
  const now = useNow(15_000);

  // Only the visible list is fetched and polled.
  const query = useQuery<MarketListResponse>({
    queryKey: ["markets", activeSubTab],
    queryFn: fetchers[activeSubTab],
    refetchInterval: 60_000,
  });

  const active = subTabs.find((t) => t.id === activeSubTab)!;
  const markets = query.data?.markets ?? [];

  return (
    <GlowingBorder color="cyan" className="p-4 sm:p-6">
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <NeonText color="cyan" size="lg">
          Markets
        </NeonText>
        <div className="flex gap-1 rounded-lg bg-dark-surface p-1" role="tablist">
          {subTabs.map((tab) => (
            <button
              key={tab.id}
              role="tab"
              aria-selected={activeSubTab === tab.id}
              onClick={() => setActiveSubTab(tab.id)}
              className={`rounded px-3 py-1.5 text-xs transition-colors ${
                activeSubTab === tab.id ? "bg-dark-lighter text-gray-100" : "text-gray-400 hover:text-gray-200"
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      <div className="mb-4 flex flex-wrap items-center justify-between gap-2 text-xs text-gray-500">
        <span>{active.blurb}</span>
        {query.data && (
          <span>
            {markets.length} events, updated {timeAgo(query.data.fetched_at, now)}
          </span>
        )}
      </div>

      {query.isPending ? (
        <LoadingState what="markets" />
      ) : query.isError && !query.data ? (
        <ErrorState what="markets" error={query.error} onRetry={() => query.refetch()} />
      ) : (
        <>
          {query.isError && <StaleNotice error={query.error} />}
          {markets.length === 0 ? (
            <EmptyState title="No markets in this list right now." />
          ) : (
            <div className="max-h-[640px] space-y-3 overflow-y-auto pr-1">
              {markets.map((market) => (
                <MarketCard key={market.id} market={market} now={now} />
              ))}
            </div>
          )}
        </>
      )}

      <p className="mt-4 border-t border-dark-border pt-3 text-xs text-gray-500">{active.tip}</p>
    </GlowingBorder>
  );
}
