// Market Intelligence Signal types
// These are derived from real Polymarket activity, not news

export interface MarketSignal {
  id: string;
  type: "whale_trade" | "price_spike" | "volume_surge";
  title: string;
  summary: string;
  market_question: string;
  market_url: string;
  signal: "BUY_YES" | "BUY_NO" | "SELL_YES" | "SELL_NO" | "WATCH";
  confidence: number; // 0-1
  current_price: number | null;
  reasoning: string;
  detected_at: string;
}

// Backward compatibility - NewsItem is now just a signal
export type NewsItem = MarketSignal;
