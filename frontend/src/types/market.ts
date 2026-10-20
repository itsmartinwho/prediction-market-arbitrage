export interface MarketNews {
  title: string;
  source: string;
  url: string;
}

export interface MarketSummary {
  id: string;
  title: string; // the event's title
  slug: string | null;
  yes_price: number | null;
  no_price: number | null;
  volume: number;
  volume_24h: number;
  liquidity: number;
  end_date: string | null;
  market_count: number; // how many markets (outcomes) the event has
  polymarket_url: string;
  news: MarketNews | null;
}

export interface MarketListResponse {
  markets: MarketSummary[];
  count: number;
  fetched_at: string; // when the API last asked Polymarket for this list
}
