"use client";

import { useQuery } from "@tanstack/react-query";
import { GlowingBorder } from "../shared/GlowingBorder";
import { NeonText } from "../shared/NeonText";
import { EmptyState, ErrorState, LoadingState, StaleNotice } from "../shared/QueryState";
import { fetchWhaleActivity } from "@/lib/api";
import { formatUSD, timeAgo } from "@/lib/format";
import { useNow } from "@/hooks/useNow";
import { WhaleActivity } from "@/types/whale";

function TradeCard({ trade, now }: { trade: WhaleActivity; now: number }) {
  const isBuy = trade.action === "BUY";

  return (
    <a
      href={trade.polymarket_url}
      target="_blank"
      rel="noopener noreferrer"
      className="group block rounded-lg border border-dark-border bg-dark-surface p-4 transition-colors hover:border-gray-500"
    >
      <div className="mb-2 flex items-center justify-between gap-2">
        <div className="flex min-w-0 flex-wrap items-center gap-2">
          <span className="truncate text-sm font-medium text-neon-magenta">{trade.trader_name}</span>
          <span
            className={`rounded px-2 py-0.5 font-mono text-xs ${
              isBuy ? "bg-neon-green/15 text-neon-green" : "bg-neon-red/15 text-neon-red"
            }`}
          >
            {trade.action}
          </span>
          <span className="rounded bg-dark-lighter px-2 py-0.5 font-mono text-xs text-gray-300">
            {trade.outcome}
          </span>
        </div>
        <time
          className="shrink-0 text-xs text-gray-500"
          dateTime={trade.timestamp}
          title={new Date(trade.timestamp).toLocaleString()}
        >
          {timeAgo(trade.timestamp, now)}
        </time>
      </div>

      <p className="mb-3 line-clamp-2 text-sm text-gray-200 group-hover:text-white">{trade.market_question}</p>

      <div className="flex items-center justify-between text-xs">
        <div className="flex items-center gap-4 text-gray-500">
          <span>
            <span className="font-mono text-gray-300">{Math.round(trade.size).toLocaleString()}</span> shares
          </span>
          <span>
            at <span className="font-mono text-gray-300">{(trade.price * 100).toFixed(1)}¢</span>
          </span>
        </div>
        <span className={`font-mono font-semibold ${isBuy ? "text-neon-green" : "text-neon-red"}`}>
          {formatUSD(trade.usd_value)}
        </span>
      </div>
    </a>
  );
}

export function WhaleTracker() {
  const now = useNow(5_000);
  const query = useQuery<WhaleActivity[]>({
    queryKey: ["whale-activity"],
    queryFn: () => fetchWhaleActivity(30),
    refetchInterval: 30_000,
  });

  const trades = query.data ?? [];

  return (
    <GlowingBorder color="magenta" className="p-4 sm:p-6">
      <div className="mb-4 flex items-center justify-between">
        <NeonText color="magenta" size="lg">
          Whale trades
        </NeonText>
        <span className="text-xs text-gray-500">
          {query.data ? `${trades.length} of the latest trades of $1,000 or more, largest first` : "Trades of $1,000 or more"}
        </span>
      </div>

      {query.isPending ? (
        <LoadingState what="recent trades" />
      ) : query.isError && !query.data ? (
        <ErrorState what="recent trades" error={query.error} onRetry={() => query.refetch()} />
      ) : (
        <>
          {query.isError && <StaleNotice error={query.error} />}
          {trades.length === 0 ? (
            <EmptyState title="No trades of $1,000 or more among the latest." />
          ) : (
            <div className="max-h-[600px] space-y-3 overflow-y-auto pr-1">
              {trades.map((trade, index) => (
                <TradeCard key={`${trade.transaction_hash || index}-${trade.timestamp}`} trade={trade} now={now} />
              ))}
            </div>
          )}
        </>
      )}

      <p className="mt-4 border-t border-dark-border pt-3 text-xs text-gray-500">
        From Polymarket&apos;s Data API. The time is when the trade happened. Each opens its market on Polymarket.
      </p>
    </GlowingBorder>
  );
}
