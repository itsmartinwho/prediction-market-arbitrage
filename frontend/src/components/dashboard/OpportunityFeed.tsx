"use client";

import { GlowingBorder } from "../shared/GlowingBorder";
import { NeonText } from "../shared/NeonText";
import { EmptyState, ErrorState, LoadingState, StaleNotice } from "../shared/QueryState";
import { OpportunityCard } from "./OpportunityCard";
import { useOpportunities, useStatus } from "@/hooks/useDashboard";
import { useNow } from "@/hooks/useNow";
import { timeAgo } from "@/lib/format";
import { OpportunitiesResponse } from "@/types/opportunity";

function Row({ label, value, tone = "text-gray-300" }: { label: string; value: number | string; tone?: string }) {
  return (
    <div className="flex justify-between gap-4">
      <span className="text-gray-500">{label}</span>
      <span className={`font-mono ${tone}`}>{value}</span>
    </div>
  );
}

function Diagnostics({ scan }: { scan: OpportunitiesResponse }) {
  const d = scan.diagnostics;
  const priced = d.total_markets - d.filtered_no_clob_liquidity;
  return (
    <div className="mb-4 rounded-lg border border-dark-border bg-dark-surface p-4 text-xs">
      <div className="mb-3 font-medium text-gray-400">What the last scan saw</div>
      <div className="grid grid-cols-1 gap-x-8 gap-y-2 sm:grid-cols-2">
        <Row label="Markets scanned" value={d.total_markets} />
        <Row label="With prices" value={priced} />
        <Row label="Priced from order books" value={priced - d.used_gamma_fallback} />
        <Row label="Gamma price fallback" value={d.used_gamma_fallback} tone="text-neon-yellow" />
        <Row label="YES + NO at or above $1 after fee" value={d.filtered_not_profitable} />
        <Row label={`Under the ${d.threshold_percent}% threshold`} value={d.filtered_below_threshold} />
        {d.clob_errors > 0 && <Row label="Order book errors" value={d.clob_errors} tone="text-neon-red" />}
        <Row label="Scan took" value={`${(scan.scan_time_ms / 1000).toFixed(1)}s`} />
      </div>
      <p className="mt-3 border-t border-dark-border pt-3 text-gray-500">
        A fallback uses the price Gamma lists (last or mid), which you cannot necessarily buy at. It happens when one
        side of a book has no asks.
      </p>
    </div>
  );
}

export function OpportunityFeed() {
  const scan = useOpportunities();
  const status = useStatus();
  const now = useNow(1_000);
  const data = scan.data;

  const howOften =
    status.data?.mode === "continuous"
      ? `every ${status.data.scan_interval_seconds}s after the last scan ends`
      : `on request, at most once every ${status.data?.cache_ttl_seconds ?? 30}s`;

  return (
    <GlowingBorder color="green" className="p-4 sm:p-6">
      <div className="mb-4 flex flex-wrap items-center justify-between gap-2">
        <NeonText color="green" size="lg">
          Arbitrage
        </NeonText>
        {data && (
          <span className="text-xs text-gray-500">
            {data.count} found in the {data.markets_scanned} most liquid two-outcome markets, scanned{" "}
            {timeAgo(data.scanned_at, now)}
          </span>
        )}
      </div>

      {scan.isPending ? (
        <LoadingState what="order books for the arbitrage scan" />
      ) : scan.isError && !data ? (
        <ErrorState what="the arbitrage scan" error={scan.error} onRetry={() => scan.refetch()} />
      ) : data ? (
        <>
          {scan.isError && <StaleNotice error={scan.error} />}
          {data.count === 0 ? (
            <>
              <EmptyState
                title="No YES + NO pair under $1 after the fee right now."
                hint="That is the usual result: Polymarket's liquid markets are priced tightly, and an edge, when one appears, tends to close within seconds."
              />
              <Diagnostics scan={data} />
            </>
          ) : (
            <>
              <div className="space-y-4">
                {data.opportunities.map((opp) => (
                  <OpportunityCard key={opp.id} opportunity={opp} />
                ))}
              </div>
              <div className="mt-4">
                <Diagnostics scan={data} />
              </div>
            </>
          )}
        </>
      ) : null}

      <div className="mt-4 space-y-1 border-t border-dark-border pt-3 text-xs text-gray-500">
        <p>
          In a two-outcome market one side pays $1.00. If the best YES ask plus the best NO ask costs less than $1.00
          minus the assumed ${(data?.fee ?? 0.02).toFixed(2)} fee, buying both locks in the difference.
        </p>
        <p>
          It scans the {status.data?.market_limit ?? 200} most liquid markets {howOften}, and lists edges of{" "}
          {data?.diagnostics.threshold_percent ?? 1}% or more. Slippage and depth are not modelled.
        </p>
      </div>
    </GlowingBorder>
  );
}
