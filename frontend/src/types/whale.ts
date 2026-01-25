export interface Whale {
  address: string;
  name: string | null;
  profit_loss: number;
  volume: number;
  positions_count: number;
  win_rate: number | null;
}

export interface WhaleActivity {
  whale_address: string;
  whale_name: string | null;
  market_id: string;
  market_question: string;
  action: "BUY" | "SELL";
  outcome: "Yes" | "No";
  shares: number;
  price: number;
  timestamp: string;
  usd_value: number;
}
