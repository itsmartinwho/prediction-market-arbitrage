export interface WhaleActivity {
  trader_name: string;
  trader_address: string | null;
  market_question: string;
  market_slug: string;
  action: "BUY" | "SELL";
  outcome: string;
  size: number;
  price: number;
  usd_value: number;
  timestamp: string;
  polymarket_url: string;
  transaction_hash: string | null;
}
