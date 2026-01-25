export interface NewsItem {
  id: string;
  title: string;
  summary: string;
  source: string;
  url: string;
  published_at: string;
  relevance_score: number;
  sentiment: "bullish" | "bearish" | "neutral";
  related_markets: string[];
  keywords: string[];
}

export interface MarketSignal {
  news_id: string;
  news_title: string;
  market_id: string;
  market_question: string;
  signal: "BUY_YES" | "BUY_NO" | "SELL_YES" | "SELL_NO";
  confidence: number;
  current_price: number | null;
  target_price: number | null;
  reasoning: string;
  detected_at: string;
}
