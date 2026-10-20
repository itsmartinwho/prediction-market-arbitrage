"use client";

import { useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { GlowingBorder } from "../shared/GlowingBorder";
import { NeonText } from "../shared/NeonText";
import { EmptyState, ErrorState, LoadingState, StaleNotice } from "../shared/QueryState";
import { MarketCard } from "./MarketCard";
import { fetchHotMarkets, searchMarkets } from "@/lib/api";
import { useNow } from "@/hooks/useNow";
import { MarketListResponse } from "@/types/market";

// Each category searches one representative word.
const CATEGORIES = [
  { id: "all", label: "All", query: "" },
  { id: "politics", label: "Politics", query: "election" },
  { id: "crypto", label: "Crypto", query: "bitcoin" },
  { id: "sports", label: "Sports", query: "nba" },
  { id: "economy", label: "Economy", query: "fed" },
];

export function MarketExplorer() {
  const [input, setInput] = useState("");
  const [debounced, setDebounced] = useState("");
  const [category, setCategory] = useState("all");
  const now = useNow(15_000);

  useEffect(() => {
    const id = setTimeout(() => setDebounced(input.trim()), 350);
    return () => clearTimeout(id);
  }, [input]);

  const categoryQuery = CATEGORIES.find((c) => c.id === category)?.query ?? "";
  const query = debounced || categoryQuery;

  const result = useQuery<MarketListResponse>({
    queryKey: ["search", query],
    queryFn: () => (query ? searchMarkets(query, 30) : fetchHotMarkets(30)),
    refetchInterval: 60_000,
  });

  const markets = result.data?.markets ?? [];

  return (
    <GlowingBorder color="yellow" className="p-4 sm:p-6">
      <div className="mb-4 flex items-center justify-between">
        <NeonText color="yellow" size="lg">
          Search
        </NeonText>
        <span className="text-xs text-gray-500">Open Polymarket events</span>
      </div>

      <label className="mb-3 block">
        <span className="sr-only">Search markets</span>
        <input
          type="search"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Search markets, e.g. trump, bitcoin, super bowl"
          maxLength={100}
          className="w-full rounded-lg border border-dark-border bg-dark-surface px-4 py-3 text-sm text-gray-100 placeholder-gray-500 transition-colors focus:border-neon-yellow/60 focus:outline-none"
        />
      </label>

      <div className="mb-4 flex flex-wrap gap-2">
        {CATEGORIES.map((c) => (
          <button
            key={c.id}
            onClick={() => {
              setCategory(c.id);
              setInput("");
              setDebounced("");
            }}
            className={`rounded px-3 py-1.5 text-xs transition-colors ${
              category === c.id && !debounced
                ? "border border-neon-yellow/50 bg-neon-yellow/10 text-neon-yellow"
                : "border border-dark-border bg-dark-surface text-gray-400 hover:border-gray-500"
            }`}
          >
            {c.label}
          </button>
        ))}
      </div>

      <div className="mb-4 flex items-center justify-between text-xs text-gray-500">
        <span>{query ? `Results for "${query}"` : "The most traded events"}</span>
        {result.data && <span>{markets.length} events</span>}
      </div>

      {result.isPending ? (
        <LoadingState what={query ? `results for "${query}"` : "markets"} />
      ) : result.isError && !result.data ? (
        <ErrorState what="search results" error={result.error} onRetry={() => result.refetch()} />
      ) : (
        <>
          {result.isError && <StaleNotice error={result.error} />}
          {markets.length === 0 ? (
            <EmptyState title={`No open events match "${query}".`} hint="Try a shorter or more general word." />
          ) : (
            <div className="max-h-[600px] space-y-2 overflow-y-auto pr-1">
              {markets.map((market) => (
                <MarketCard key={market.id} market={market} now={now} />
              ))}
            </div>
          )}
        </>
      )}
    </GlowingBorder>
  );
}
