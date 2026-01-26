"use client";

import { PulsingDot } from "../shared/PulsingDot";

interface ScannerStats {
  running: boolean;
  scan_count: number;
  last_scan: string | null;
  active_opportunities: number;
  total_seen: number;
}

interface StatsStripProps {
  stats: ScannerStats | null;
  opportunityCount: number;
  isConnected: boolean;
}

export function StatsStrip({
  stats,
  opportunityCount,
  isConnected,
}: StatsStripProps) {
  const isRunning = stats?.running ?? false;
  const scanCount = stats?.scan_count ?? 0;
  const lastScan = stats?.last_scan
    ? new Date(stats.last_scan).toLocaleTimeString()
    : "N/A";

  return (
    <div className="flex items-center gap-1 text-xs font-mono">
      {/* Scanner Status */}
      <div className="flex items-center gap-1.5">
        <PulsingDot color={isRunning ? "green" : "red"} size="sm" />
        <span className="text-gray-400">SCANNER:</span>
        <span className={isRunning ? "text-neon-green" : "text-neon-red"}>
          {isRunning ? "ACTIVE" : "OFFLINE"}
        </span>
        <span className="text-gray-500">({scanCount})</span>
      </div>

      <span className="text-dark-border mx-2">|</span>

      {/* Opportunities */}
      <div className="flex items-center gap-1.5">
        <span className="text-gray-400">OPPS:</span>
        <span
          className={
            opportunityCount > 0 ? "text-neon-yellow" : "text-gray-500"
          }
        >
          {opportunityCount}
        </span>
      </div>

      <span className="text-dark-border mx-2">|</span>

      {/* WebSocket Status */}
      <div className="flex items-center gap-1.5">
        <PulsingDot color={isConnected ? "green" : "red"} size="sm" />
        <span className="text-gray-400">WS:</span>
        <span className={isConnected ? "text-neon-green" : "text-neon-red"}>
          {isConnected ? "LIVE" : "OFF"}
        </span>
      </div>

      <span className="text-dark-border mx-2">|</span>

      {/* Last Scan */}
      <div className="flex items-center gap-1.5">
        <span className="text-gray-400">LAST:</span>
        <span className="text-neon-cyan">{lastScan}</span>
      </div>
    </div>
  );
}
