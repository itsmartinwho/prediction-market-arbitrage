export function formatUSD(value: number): string {
  if (value >= 1_000_000) return `$${(value / 1_000_000).toFixed(1)}M`;
  if (value >= 1_000) return `$${(value / 1_000).toFixed(1)}K`;
  return `$${value.toFixed(0)}`;
}

export function formatCents(price: number | null): string {
  if (price === null || price === undefined) return "n/a";
  return `${(price * 100).toFixed(price < 0.01 || price > 0.99 ? 1 : 0)}¢`;
}

/** "just now", "42s ago", "5m ago", "3h ago", "2d ago" */
export function timeAgo(iso: string | null | undefined, now: number = Date.now()): string {
  if (!iso) return "never";
  const seconds = Math.max(0, Math.round((now - new Date(iso).getTime()) / 1000));
  if (seconds < 5) return "just now";
  if (seconds < 60) return `${seconds}s ago`;
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  return `${Math.floor(hours / 24)}d ago`;
}

/** "3d 4h", "5h", "12m", or "Ended" */
export function timeLeft(iso: string | null, now: number = Date.now()): string {
  if (!iso) return "";
  const ms = new Date(iso).getTime() - now;
  if (ms <= 0) return "Ended";
  const days = Math.floor(ms / 86_400_000);
  const hours = Math.floor((ms % 86_400_000) / 3_600_000);
  if (days > 30) return `${Math.floor(days / 30)}mo`;
  if (days > 0) return `${days}d ${hours}h`;
  if (hours > 0) return `${hours}h`;
  return `${Math.max(1, Math.floor((ms % 3_600_000) / 60_000))}m`;
}
