"use client";

import { GlowingBorder } from "../shared/GlowingBorder";
import { NeonText } from "../shared/NeonText";
import { PulsingDot } from "../shared/PulsingDot";
import { ScannerStats } from "@/types/opportunity";

interface StatsCardsProps {
  stats: ScannerStats | null;
  opportunityCount: number;
  isConnected: boolean;
}

export function StatsCards({
  stats,
  opportunityCount,
  isConnected,
}: StatsCardsProps) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
      {/* Scanner Status */}
      <GlowingBorder color={stats?.running ? "green" : "red"} className="p-4">
        <div className="flex items-center justify-between mb-2">
          <span className="text-gray-400 text-sm">SCANNER</span>
          <PulsingDot color={stats?.running ? "green" : "red"} size="sm" />
        </div>
        <NeonText color={stats?.running ? "green" : "cyan"} size="xl">
          {stats?.running ? "ACTIVE" : "OFFLINE"}
        </NeonText>
        <div className="text-gray-500 text-xs mt-1">
          {stats?.scan_count || 0} scans completed
        </div>
      </GlowingBorder>

      {/* Active Opportunities */}
      <GlowingBorder
        color={opportunityCount > 0 ? "magenta" : "cyan"}
        className="p-4"
      >
        <div className="flex items-center justify-between mb-2">
          <span className="text-gray-400 text-sm">OPPORTUNITIES</span>
          {opportunityCount > 0 && <PulsingDot color="cyan" size="sm" />}
        </div>
        <NeonText color={opportunityCount > 0 ? "magenta" : "cyan"} size="xl">
          {opportunityCount}
        </NeonText>
        <div className="text-gray-500 text-xs mt-1">
          {stats?.total_seen || 0} total detected
        </div>
      </GlowingBorder>

      {/* WebSocket Status */}
      <GlowingBorder color={isConnected ? "green" : "red"} className="p-4">
        <div className="flex items-center justify-between mb-2">
          <span className="text-gray-400 text-sm">WEBSOCKET</span>
          <PulsingDot color={isConnected ? "green" : "red"} size="sm" />
        </div>
        <NeonText color={isConnected ? "green" : "cyan"} size="xl">
          {isConnected ? "CONNECTED" : "DISCONNECTED"}
        </NeonText>
        <div className="text-gray-500 text-xs mt-1">Real-time updates</div>
      </GlowingBorder>

      {/* Last Scan */}
      <GlowingBorder className="p-4">
        <div className="flex items-center justify-between mb-2">
          <span className="text-gray-400 text-sm">LAST SCAN</span>
        </div>
        <NeonText color="cyan" size="lg">
          {stats?.last_scan
            ? new Date(stats.last_scan).toLocaleTimeString()
            : "N/A"}
        </NeonText>
        <div className="text-gray-500 text-xs mt-1">
          Scanning every 5 seconds
        </div>
      </GlowingBorder>
    </div>
  );
}
