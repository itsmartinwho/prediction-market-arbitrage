"use client";

import { useQuery } from "@tanstack/react-query";
import { GlowingBorder } from "../shared/GlowingBorder";
import { NeonText } from "../shared/NeonText";
import { EmptyState, ErrorState, LoadingState, StaleNotice } from "../shared/QueryState";
import { fetchSignals } from "@/lib/api";
import { timeAgo } from "@/lib/format";
import { useNow } from "@/hooks/useNow";
import { MarketSignal } from "@/types/news";

const TYPE_LABEL: Record<string, string> = {
  whale_trade: "Large trade",
  price_spike: "Extreme price",
  volume_surge: "High volume",
};

function signalTone(signal: string): string {
  if (signal.startsWith("BUY")) return "bg-neon-green/15 text-neon-green";
  if (signal.startsWith("SELL")) return "bg-neon-red/15 text-neon-red";
  return "bg-dark-lighter text-gray-300";
}

function SignalCard({ signal, now }: { signal: MarketSignal; now: number }) {
  return (
    <a
      href={signal.market_url}
      target="_blank"
      rel="noopener noreferrer"
      className="group block rounded-lg border border-dark-border bg-dark-surface p-4 transition-colors hover:border-gray-500"
    >
      <div className="mb-2 flex items-start justify-between gap-2">
        <div className="flex flex-wrap items-center gap-2 text-xs">
          <span className="text-gray-400">{TYPE_LABEL[signal.type] ?? "Signal"}</span>
          <span className={`rounded px-2 py-0.5 font-mono ${signalTone(signal.signal)}`}>
            {signal.signal.replace(/_/g, " ")}
          </span>
          <span className="text-gray-500">{(signal.confidence * 100).toFixed(0)}% weight</span>
        </div>
        <span className="shrink-0 text-xs text-gray-500">{timeAgo(signal.detected_at, now)}</span>
      </div>

      <h3 className="mb-1 text-sm font-medium text-neon-orange">{signal.title}</h3>
      <p className="mb-2 line-clamp-2 text-xs text-gray-300">{signal.market_question}</p>
      <p className="mb-2 text-xs text-gray-500">{signal.summary}</p>
      <p className="border-l-2 border-dark-lighter pl-2 text-xs text-gray-500">{signal.reasoning}</p>
    </a>
  );
}

export function SignalsFeed() {
  const now = useNow(15_000);
  const query = useQuery<MarketSignal[]>({
    queryKey: ["market-signals"],
    queryFn: () => fetchSignals(20),
    refetchInterval: 60_000,
  });

  const signals = query.data ?? [];

  return (
    <GlowingBorder color="orange" className="p-4 sm:p-6">
      <div className="mb-4 flex items-center justify-between">
        <NeonText color="orange" size="lg">
          Signals
        </NeonText>
        <span className="text-xs text-gray-500">Rules of thumb, not predictions</span>
      </div>

      {query.isPending ? (
        <LoadingState what="signals" />
      ) : query.isError && !query.data ? (
        <ErrorState what="signals" error={query.error} onRetry={() => query.refetch()} />
      ) : (
        <>
          {query.isError && <StaleNotice error={query.error} />}
          {signals.length === 0 ? (
            <EmptyState
              title="No signals right now."
              hint="A signal is a trade over $5,000, a market above 90% or below 10%, or one with over $100,000 of volume."
            />
          ) : (
            <div className="max-h-[600px] space-y-3 overflow-y-auto pr-1">
              {signals.map((signal) => (
                <SignalCard key={signal.id} signal={signal} now={now} />
              ))}
            </div>
          )}
        </>
      )}

      <p className="mt-4 border-t border-dark-border pt-3 text-xs text-gray-500">
        Read off the same live data: large trades, extreme prices and high volume. The weight is a heuristic, not a
        probability.
      </p>
    </GlowingBorder>
  );
}
