export interface Opportunity {
  id: string;
  type: "yes_no" | "cross_platform";
  market_id: string;
  market_question: string;
  yes_price: number;
  no_price: number;
  combined_cost: number;
  gross_profit: number;
  net_profit: number;
  edge_percent: number;
  yes_token_id?: string | null;
  no_token_id?: string | null;
  detected_at: string;
  platform: string;
}

export interface ScanDiagnostics {
  total_markets: number;
  filtered_not_binary: number;
  filtered_no_tokens: number;
  filtered_no_clob_liquidity: number;
  clob_errors: number;
  used_gamma_fallback: number;
  filtered_not_profitable: number;
  filtered_below_threshold: number;
  opportunities_found: number;
  threshold_percent: number;
}

export type ScannerMode = "on_request" | "continuous";

export interface OpportunitiesResponse {
  opportunities: Opportunity[];
  count: number;
  scan_time_ms: number;
  scanned_at: string;
  markets_scanned: number;
  market_limit: number;
  mode: ScannerMode;
  fee: number;
  diagnostics: ScanDiagnostics;
}

export interface ApiStatus {
  status: "ok";
  version: string;
  mode: ScannerMode;
  on_vercel: boolean;
  market_limit: number;
  cache_ttl_seconds: number;
  scan_interval_seconds: number | null;
  min_profit_threshold: number;
  fee: number;
  alerts: "off" | "console" | "telegram";
}
