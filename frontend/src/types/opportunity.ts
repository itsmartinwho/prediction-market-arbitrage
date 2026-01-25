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
  yes_token_id?: string;
  no_token_id?: string;
  detected_at: string;
  platform: string;
}

export interface OpportunitiesResponse {
  opportunities: Opportunity[];
  count: number;
  scan_time_ms: number;
}

export interface ScannerStats {
  running: boolean;
  scan_count: number;
  last_scan: string | null;
  active_opportunities: number;
  total_seen: number;
}
