"use client";

import { Opportunity } from "@/types/opportunity";

export function OpportunityCard({
  opportunity,
  customFee,
}: {
  opportunity: Opportunity;
  customFee?: number;
}) {
  const grossProfit = 1.0 - opportunity.combined_cost;
  const effectiveNet =
    customFee !== undefined ? grossProfit - customFee : opportunity.net_profit;
  const effectiveEdge =
    opportunity.combined_cost > 0
      ? (effectiveNet / opportunity.combined_cost) * 100
      : 0;
  const lowEdge = effectiveEdge < 2;

  return (
    <article className="rounded-lg border border-neon-green/30 bg-dark-surface p-4">
      <div className="mb-3 flex items-start justify-between gap-4">
        <div className="space-y-1">
          <h3 className="line-clamp-2 text-sm font-medium leading-tight text-gray-100">
            {opportunity.market_question}
          </h3>
          <div className="flex flex-wrap items-center gap-2 text-[11px]">
            <span
              className={`rounded px-1.5 py-0.5 font-mono ${
                opportunity.used_fallback
                  ? "border border-neon-yellow/30 bg-neon-yellow/10 text-neon-yellow"
                  : "border border-dark-border bg-dark-lighter text-gray-300"
              }`}
            >
              {opportunity.used_fallback ? "Gamma Fallback Price" : "CLOB Order Book"}
            </span>
            {opportunity.best_ask_size != null && (
              <span className="font-mono text-gray-400 tabular-nums">
                Top ask size: {opportunity.best_ask_size.toLocaleString()} sh
              </span>
            )}
          </div>
        </div>
        <span className="shrink-0 rounded bg-neon-green/15 px-2.5 py-1 font-mono text-xs font-semibold text-neon-green tabular-nums">
          +{effectiveEdge.toFixed(2)}% edge
        </span>
      </div>

      {lowEdge && (
        <p className="mb-3 rounded border border-neon-yellow/25 bg-neon-yellow/5 p-2 text-xs text-neon-yellow">
          Under 2%: depth, slippage and the real fee can erase it.
        </p>
      )}

      <div className="mb-3 grid grid-cols-2 gap-4 text-xs sm:grid-cols-4">
        <div>
          <div className="mb-1 text-gray-500">YES best ask</div>
          <div className="font-mono text-neon-green tabular-nums">${opportunity.yes_price.toFixed(4)}</div>
        </div>
        <div>
          <div className="mb-1 text-gray-500">NO best ask</div>
          <div className="font-mono text-neon-red tabular-nums">${opportunity.no_price.toFixed(4)}</div>
        </div>
        <div>
          <div className="mb-1 text-gray-500">Combined cost</div>
          <div className="font-mono text-gray-200 tabular-nums">${opportunity.combined_cost.toFixed(4)}</div>
        </div>
        <div>
          <div className="mb-1 text-gray-500">Max executable capacity</div>
          <div className="font-mono text-gray-200 tabular-nums">
            {opportunity.max_executable_size != null
              ? `${opportunity.max_executable_size.toLocaleString()} sh ($${(opportunity.max_executable_profit ?? 0).toFixed(2)} net)`
              : opportunity.best_ask_size != null
                ? `${opportunity.best_ask_size.toLocaleString()} sh (top level)`
                : "—"}
          </div>
        </div>
      </div>

      <div className="flex flex-wrap items-center justify-between gap-2 border-t border-dark-border pt-3 text-xs">
        <div className="flex flex-wrap items-center gap-4">
          <span>
            <span className="text-gray-500">Net per $1 payout </span>
            <span className="font-mono text-neon-green tabular-nums">${effectiveNet.toFixed(4)}</span>
          </span>
          {opportunity.vwap_combined_cost != null && (
            <span>
              <span className="text-gray-500">Book VWAP </span>
              <span className="font-mono text-gray-300 tabular-nums">${opportunity.vwap_combined_cost.toFixed(4)}</span>
            </span>
          )}
        </div>
        <span className="text-gray-500 tabular-nums">seen {new Date(opportunity.detected_at).toLocaleTimeString()}</span>
      </div>
    </article>
  );
}
