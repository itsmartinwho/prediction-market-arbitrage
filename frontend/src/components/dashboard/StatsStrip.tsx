"use client";

import { useIsFetching, useQueryClient } from "@tanstack/react-query";
import { useOpportunities, useStatus } from "@/hooks/useDashboard";
import { useNow } from "@/hooks/useNow";
import { describeError } from "@/lib/api";
import { timeAgo } from "@/lib/format";

type Tone = "green" | "yellow" | "red" | "muted";

const dot: Record<Tone, string> = {
  green: "bg-neon-green",
  yellow: "bg-neon-yellow",
  red: "bg-neon-red",
  muted: "bg-gray-500",
};

const text: Record<Tone, string> = {
  green: "text-neon-green",
  yellow: "text-neon-yellow",
  red: "text-neon-red",
  muted: "text-gray-400",
};

/**
 * What the dashboard can honestly say under polling: whether the API answers,
 * how old the latest scan is, and how this deployment scans.
 */
export function StatsStrip() {
  const status = useStatus();
  const scan = useOpportunities();
  const queryClient = useQueryClient();
  const fetching = useIsFetching();
  const now = useNow(1000);

  const ttl = status.data?.cache_ttl_seconds ?? 30;
  const scannedAt = scan.data?.scanned_at;
  const ageSeconds = scannedAt ? (now - new Date(scannedAt).getTime()) / 1000 : null;

  let api: { tone: Tone; label: string; title?: string };
  if (status.isPending) {
    api = { tone: "muted", label: "Connecting" };
  } else if (status.isError && !status.data) {
    api = { tone: "red", label: "API unreachable", title: describeError(status.error) };
  } else if (scan.isError && !scan.data) {
    api = { tone: "red", label: "Polymarket unavailable", title: describeError(scan.error) };
  } else if (scan.isError || (ageSeconds !== null && ageSeconds > ttl * 4 + 60)) {
    api = { tone: "yellow", label: "Stale", title: "The latest refresh failed or is overdue" };
  } else {
    api = { tone: "green", label: "Live" };
  }

  const mode = status.data
    ? status.data.mode === "continuous"
      ? `Continuous scan, every ${status.data.scan_interval_seconds}s`
      : `Scans on request, cached ${status.data.cache_ttl_seconds}s`
    : null;

  let scanText = "Scanning…";
  if (scan.data) {
    const n = scan.data.count;
    scanText = `${scan.data.markets_scanned} markets, ${n} ${n === 1 ? "opportunity" : "opportunities"}, ${timeAgo(scannedAt, now)}`;
  } else if (scan.isError) {
    scanText = "No scan yet";
  }

  return (
    <div className="flex flex-wrap items-center gap-x-4 gap-y-2 text-xs lg:max-w-[52%] lg:justify-end lg:pt-1">
      <span className="flex items-center gap-1.5" title={api.title}>
        <span className={`h-2 w-2 rounded-full ${dot[api.tone]}`} aria-hidden />
        <span className={text[api.tone]}>{api.label}</span>
      </span>
      <span className="text-gray-400">
        <span className="text-gray-500">Last scan: </span>
        {scanText}
      </span>
      {mode && <span className="hidden text-gray-500 md:inline">{mode}</span>}
      <button
        onClick={() => queryClient.invalidateQueries()}
        disabled={fetching > 0}
        className="cyber-button text-xs disabled:cursor-wait disabled:opacity-60"
        title="Ask the API again. It answers from its cache when that is fresh."
      >
        {fetching > 0 ? "Refreshing…" : "Refresh"}
      </button>
    </div>
  );
}
