"use client";

import { useState } from "react";
import { GlowingBorder } from "../shared/GlowingBorder";
import { NeonText } from "../shared/NeonText";
import { EmptyState, ErrorState, LoadingState, StaleNotice } from "../shared/QueryState";
import { OpportunityCard } from "./OpportunityCard";
import { useOpportunities, useStatus } from "@/hooks/useDashboard";
import { useNow } from "@/hooks/useNow";
import { timeAgo } from "@/lib/format";
import { ClosestMarket, OpportunitiesResponse } from "@/types/opportunity";

function Row({ label, value, tone = "text-gray-300" }: { label: string; value: number | string; tone?: string }) {
  return (
    <div className="flex justify-between gap-4">
      <span className="text-gray-500">{label}</span>
      <span className={`font-mono tabular-nums ${tone}`}>{value}</span>
    </div>
  );
}

function ClosestMarketsTable({
  markets,
  assumedFee,
  minEdgePct,
}: {
  markets: ClosestMarket[];
  assumedFee: number;
  minEdgePct: number;
}) {
  if (!markets || markets.length === 0) return null;

  return (
    <div className="mb-4 rounded-lg border border-dark-border bg-dark-surface p-4 text-xs">
      <div className="mb-2 flex flex-wrap items-center justify-between gap-2">
        <span className="font-medium text-gray-200">
          Near-Arb Watchlist — Tightest Binary Order Books
        </span>
        <span className="font-mono text-[11px] text-gray-500 tabular-nums">
          Break-even combined ask at ${(assumedFee).toFixed(3)} fee: ${(1 - assumedFee).toFixed(4)}
        </span>
      </div>
      <p className="mb-3 text-gray-500">
        Ranked by lowest combined YES + NO best ask across the scanned binary markets, showing how close each order book is to locking in a riskless $1.00 payout.
      </p>
      <div className="overflow-x-auto">
        <table className="w-full border-collapse text-left">
          <thead>
            <tr className="border-b border-dark-border text-[11px] uppercase tracking-wider text-gray-500">
              <th className="py-2 pr-3 font-medium">Market</th>
              <th className="px-2 py-2 text-right font-medium">YES Ask</th>
              <th className="px-2 py-2 text-right font-medium">NO Ask</th>
              <th className="px-2 py-2 text-right font-medium">Combined</th>
              <th className="px-2 py-2 text-right font-medium">Net Spread</th>
              <th className="px-2 py-2 text-right font-medium">Dist. to Arb</th>
              <th className="pl-2 py-2 text-right font-medium">Top Size</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-dark-border/60 font-mono tabular-nums">
            {markets.map((m) => {
              const gross = 1.0 - m.combined_cost;
              const net = gross - assumedFee;
              const edgePct = m.combined_cost > 0 ? (net / m.combined_cost) * 100 : 0;
              const qualifies = net > 0 && edgePct >= minEdgePct;
              const dist = Math.max(0, m.combined_cost - (1.0 - assumedFee));
              return (
                <tr key={m.market_id} className="hover:bg-dark-lighter/40">
                  <td className="max-w-[280px] truncate py-2 pr-3 font-sans text-gray-200" title={m.market_question}>
                    {m.market_question}
                    {m.used_fallback && (
                      <span className="ml-1.5 rounded bg-neon-yellow/10 px-1 py-0.5 font-mono text-[10px] text-neon-yellow">
                        Gamma
                      </span>
                    )}
                  </td>
                  <td className="px-2 py-2 text-right text-neon-green">${m.yes_ask.toFixed(4)}</td>
                  <td className="px-2 py-2 text-right text-neon-red">${m.no_ask.toFixed(4)}</td>
                  <td className="px-2 py-2 text-right text-gray-200">${m.combined_cost.toFixed(4)}</td>
                  <td
                    className={`px-2 py-2 text-right ${
                      qualifies ? "font-semibold text-neon-green" : net > 0 ? "text-neon-yellow" : "text-gray-500"
                    }`}
                  >
                    {net >= 0 ? `+$${net.toFixed(4)}` : `-$${Math.abs(net).toFixed(4)}`}
                  </td>
                  <td className="px-2 py-2 text-right text-gray-400">
                    {dist === 0 ? (
                      <span className="text-neon-green">IN ARB</span>
                    ) : (
                      `$${dist.toFixed(4)}`
                    )}
                  </td>
                  <td className="pl-2 py-2 text-right text-gray-400">
                    {m.best_ask_size != null ? `${m.best_ask_size.toLocaleString()}` : "—"}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function Diagnostics({ scan }: { scan: OpportunitiesResponse }) {
  const d = scan.diagnostics;
  const priced = d.total_markets - d.filtered_no_clob_liquidity;
  return (
    <div className="mb-4 rounded-lg border border-dark-border bg-dark-surface p-4 text-xs">
      <div className="mb-3 font-medium text-gray-300">Scan funnel diagnostics</div>
      <div className="grid grid-cols-1 gap-x-8 gap-y-2 sm:grid-cols-2">
        <Row label="Markets scanned" value={d.total_markets} />
        <Row label="With prices" value={priced} />
        <Row label="Priced from CLOB order books" value={priced - d.used_gamma_fallback} />
        <Row label="Gamma price fallback" value={d.used_gamma_fallback} tone="text-neon-yellow" />
        <Row label="YES + NO at or above $1 after fee" value={d.filtered_not_profitable} />
        <Row label={`Under the ${d.threshold_percent}% threshold`} value={d.filtered_below_threshold} />
        {d.clob_errors > 0 && <Row label="Order book errors" value={d.clob_errors} tone="text-neon-red" />}
        <Row label="Scan latency" value={`${(scan.scan_time_ms / 1000).toFixed(1)}s`} />
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

  const [feeOverride, setFeeOverride] = useState<number | null>(null);
  const [thresholdOverride, setThresholdOverride] = useState<number | null>(null);

  const effectiveFee = feeOverride ?? data?.fee ?? 0.02;
  const effectiveThresholdPct = thresholdOverride ?? data?.diagnostics.threshold_percent ?? 1.0;

  const howOften =
    status.data?.mode === "continuous"
      ? `every ${status.data.scan_interval_seconds}s after the last scan ends`
      : `on request, at most once every ${status.data?.cache_ttl_seconds ?? 30}s`;

  const filteredOpportunities = (data?.opportunities ?? []).filter((opp) => {
    const net = 1.0 - opp.combined_cost - effectiveFee;
    const edgePct = opp.combined_cost > 0 ? (net / opp.combined_cost) * 100 : 0;
    return net > 0 && edgePct >= effectiveThresholdPct;
  });

  return (
    <GlowingBorder color="green" className="p-4 sm:p-6">
      <div className="mb-4 flex flex-wrap items-center justify-between gap-2">
        <NeonText color="green" size="lg">
          Arbitrage Scanner &amp; Order Book Depth
        </NeonText>
        {data && (
          <span className="text-xs text-gray-500 tabular-nums">
            {filteredOpportunities.length} active ({data.count} at default fee) in {data.markets_scanned} binary markets, scanned{" "}
            {timeAgo(data.scanned_at, now)}
          </span>
        )}
      </div>

      {/* Interactive Client-Side Fee & Threshold Inspector */}
      <div className="mb-4 grid grid-cols-1 gap-4 rounded-lg border border-dark-border bg-dark-surface p-3.5 text-xs sm:grid-cols-2">
        <div>
          <div className="mb-1.5 flex items-center justify-between">
            <label htmlFor="fee-slider" className="text-gray-400">
              Assumed Payout Fee
            </label>
            <span className="font-mono text-gray-200 tabular-nums">
              ${effectiveFee.toFixed(3)} ({(effectiveFee * 100).toFixed(1)}%)
            </span>
          </div>
          <input
            id="fee-slider"
            type="range"
            min={0}
            max={0.03}
            step={0.0025}
            value={effectiveFee}
            onChange={(e) => setFeeOverride(parseFloat(e.target.value))}
            className="w-full accent-neon-cyan"
          />
        </div>
        <div>
          <div className="mb-1.5 flex items-center justify-between">
            <label htmlFor="edge-slider" className="text-gray-400">
              Minimum Net Edge Filter
            </label>
            <span className="font-mono text-gray-200 tabular-nums">
              {effectiveThresholdPct.toFixed(2)}%
            </span>
          </div>
          <input
            id="edge-slider"
            type="range"
            min={0}
            max={3}
            step={0.25}
            value={effectiveThresholdPct}
            onChange={(e) => setThresholdOverride(parseFloat(e.target.value))}
            className="w-full accent-neon-cyan"
          />
        </div>
      </div>

      {scan.isPending ? (
        <LoadingState what="order books for the arbitrage scan" />
      ) : scan.isError && !data ? (
        <ErrorState what="the arbitrage scan" error={scan.error} onRetry={() => scan.refetch()} />
      ) : data ? (
        <>
          {scan.isError && <StaleNotice error={scan.error} />}
          {filteredOpportunities.length === 0 ? (
            <>
              <EmptyState
                title="No YES + NO pair clears the fee and edge filter right now."
                hint="Polymarket's liquid binary books are tightly arbitraged; inspect the Near-Arb Watchlist below to see the tightest live spreads and top-of-book sizes."
              />
              {data.diagnostics.closest_markets && data.diagnostics.closest_markets.length > 0 && (
                <ClosestMarketsTable
                  markets={data.diagnostics.closest_markets}
                  assumedFee={effectiveFee}
                  minEdgePct={effectiveThresholdPct}
                />
              )}
              <Diagnostics scan={data} />
            </>
          ) : (
            <>
              <div className="space-y-4">
                {filteredOpportunities.map((opp) => (
                  <OpportunityCard key={opp.id} opportunity={opp} customFee={effectiveFee} />
                ))}
              </div>
              <div className="mt-4">
                {data.diagnostics.closest_markets && data.diagnostics.closest_markets.length > 0 && (
                  <ClosestMarketsTable
                    markets={data.diagnostics.closest_markets}
                    assumedFee={effectiveFee}
                    minEdgePct={effectiveThresholdPct}
                  />
                )}
                <Diagnostics scan={data} />
              </div>
            </>
          )}
        </>
      ) : null}

      <div className="mt-4 space-y-1 border-t border-dark-border pt-3 text-xs text-gray-500">
        <p>
          In a two-outcome market one side pays $1.00. If the best YES ask plus the best NO ask costs less than $1.00
          minus the assumed ${effectiveFee.toFixed(2)} fee, buying both locks in the difference.
        </p>
        <p>
          It scans the {status.data?.market_limit ?? 200} most liquid markets {howOften}, walks the full YES and NO ask
          ladders to compute executable share capacity and VWAP, and lists edges of{" "}
          {effectiveThresholdPct.toFixed(1)}% or more.
        </p>
      </div>
    </GlowingBorder>
  );
}
