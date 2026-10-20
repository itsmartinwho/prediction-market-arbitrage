"use client";

import { MarketSummary } from "@/types/market";
import { formatCents, formatUSD, timeLeft } from "@/lib/format";

export function MarketCard({ market, now }: { market: MarketSummary; now: number }) {
  const ends = timeLeft(market.end_date, now);

  return (
    <article className="rounded-lg border border-dark-border bg-dark-surface p-4 transition-colors hover:border-gray-500">
      <a href={market.polymarket_url} target="_blank" rel="noopener noreferrer" className="block">
        <h3 className="mb-3 line-clamp-2 text-sm font-medium text-gray-100 hover:text-neon-cyan">
          {market.title || "Untitled market"}
        </h3>
      </a>

      <div className="flex flex-wrap items-center justify-between gap-2 text-xs">
        <div className="flex items-center gap-4">
          {market.market_count === 1 ? (
            <>
              <span>
                <span className="text-gray-500">Yes </span>
                <span className="font-mono text-neon-green">{formatCents(market.yes_price)}</span>
              </span>
              <span>
                <span className="text-gray-500">No </span>
                <span className="font-mono text-neon-red">{formatCents(market.no_price)}</span>
              </span>
            </>
          ) : (
            <span className="text-gray-400">{market.market_count} outcomes</span>
          )}
        </div>
        <div className="flex items-center gap-3 text-gray-500">
          {market.volume_24h > 0 && <span>{formatUSD(market.volume_24h)} 24h</span>}
          <span>{formatUSD(market.volume)} total</span>
          {ends && <span className="text-neon-yellow">{ends === "Ended" ? ends : `ends in ${ends}`}</span>}
        </div>
      </div>

      {market.news && (
        <a
          href={market.news.url}
          target="_blank"
          rel="noopener noreferrer"
          className="mt-3 block border-t border-dark-border/60 pt-3"
        >
          <p className="line-clamp-2 text-xs text-gray-400 hover:text-gray-200">
            <span className="mr-2 text-neon-orange">News</span>
            {market.news.title}
          </p>
          <span className="mt-1 block text-xs text-gray-600">{market.news.source}</span>
        </a>
      )}
    </article>
  );
}
