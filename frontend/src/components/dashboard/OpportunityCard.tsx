"use client";

import { Opportunity } from "@/types/opportunity";

export function OpportunityCard({ opportunity }: { opportunity: Opportunity }) {
  const lowEdge = opportunity.edge_percent < 2;

  return (
    <article className="rounded-lg border border-neon-green/30 bg-dark-surface p-4">
      <div className="mb-3 flex items-start justify-between gap-4">
        <h3 className="line-clamp-2 text-sm font-medium leading-tight text-gray-100">
          {opportunity.market_question}
        </h3>
        <span className="shrink-0 rounded bg-neon-green/15 px-2 py-1 font-mono text-xs font-semibold text-neon-green">
          {opportunity.edge_percent.toFixed(2)}% edge
        </span>
      </div>

      {lowEdge && (
        <p className="mb-3 rounded border border-neon-yellow/25 bg-neon-yellow/5 p-2 text-xs text-neon-yellow">
          Under 2%: depth, slippage and the real fee can erase it.
        </p>
      )}

      <div className="mb-3 grid grid-cols-3 gap-4 text-xs">
        <div>
          <div className="mb-1 text-gray-500">YES ask</div>
          <div className="font-mono text-neon-green">${opportunity.yes_price.toFixed(4)}</div>
        </div>
        <div>
          <div className="mb-1 text-gray-500">NO ask</div>
          <div className="font-mono text-neon-red">${opportunity.no_price.toFixed(4)}</div>
        </div>
        <div>
          <div className="mb-1 text-gray-500">Together</div>
          <div className="font-mono text-gray-200">${opportunity.combined_cost.toFixed(4)}</div>
        </div>
      </div>

      <div className="flex items-center justify-between border-t border-dark-border pt-3 text-xs">
        <span>
          <span className="text-gray-500">Net per $1 payout </span>
          <span className="font-mono text-neon-green">${opportunity.net_profit.toFixed(4)}</span>
        </span>
        <span className="text-gray-500">seen {new Date(opportunity.detected_at).toLocaleTimeString()}</span>
      </div>
    </article>
  );
}
