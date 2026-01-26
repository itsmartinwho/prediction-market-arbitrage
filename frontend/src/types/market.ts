export interface MarketNews {
  title: string;
  source: string;
  url: string;
}

export interface MarketSummary {
  id: string;
  title: string;  // Event title (was "question")
  slug: string | null;
  yes_price: number | null;
  no_price: number | null;
  volume: number;
  liquidity: number;
  end_date: string | null;
  market_count: number;  // Number of outcomes in this event
  polymarket_url: string;
  news: MarketNews | null;
}

export interface MarketListResponse {
  markets: MarketSummary[];
  count: number;
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
