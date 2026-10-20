const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function fetchOpportunities() {
  const response = await fetch(`${API_URL}/api/arbitrage/opportunities`);
  if (!response.ok) {
    throw new Error("Failed to fetch opportunities");
  }
  return response.json();
}

export async function fetchScannerStats() {
  const response = await fetch(`${API_URL}/api/arbitrage/stats`);
  if (!response.ok) {
    throw new Error("Failed to fetch scanner stats");
  }
  return response.json();
}

export async function triggerScan() {
  const response = await fetch(`${API_URL}/api/arbitrage/scan`, {
    method: "POST",
  });
  if (!response.ok) {
    throw new Error("Failed to trigger scan");
  }
  return response.json();
}

export async function fetchMarkets(limit = 50, offset = 0) {
  const response = await fetch(
    `${API_URL}/api/markets?limit=${limit}&offset=${offset}`
  );
  if (!response.ok) {
    throw new Error("Failed to fetch markets");
  }
  return response.json();
}

export async function fetchMarketOrderbook(marketId: string) {
  const response = await fetch(`${API_URL}/api/markets/${marketId}/orderbook`);
  if (!response.ok) {
    throw new Error("Failed to fetch orderbook");
  }
  return response.json();
}

// Whale tracker endpoints
export async function fetchWhales(limit = 20) {
  const response = await fetch(`${API_URL}/api/whales?limit=${limit}`);
  if (!response.ok) {
    throw new Error("Failed to fetch whales");
  }
  return response.json();
}

export async function fetchWhaleActivity(limit = 20) {
  const response = await fetch(`${API_URL}/api/whales/activity?limit=${limit}`);
  if (!response.ok) {
    throw new Error("Failed to fetch whale activity");
  }
  return response.json();
}

// Signals endpoints (served under /api/news)
export async function fetchNews(limit = 20) {
  const response = await fetch(`${API_URL}/api/news?limit=${limit}`);
  if (!response.ok) {
    throw new Error("Failed to fetch news");
  }
  return response.json();
}

export async function fetchNewsSignals() {
  const response = await fetch(`${API_URL}/api/news/signals`);
  if (!response.ok) {
    throw new Error("Failed to fetch news signals");
  }
  return response.json();
}

// Market Activity endpoints (real Polymarket data)
export async function fetchHotMarkets(limit = 20) {
  const response = await fetch(`${API_URL}/api/market-activity/hot?limit=${limit}`);
  if (!response.ok) {
    throw new Error("Failed to fetch hot markets");
  }
  return response.json();
}

export async function fetchPriceMovers(limit = 20) {
  const response = await fetch(`${API_URL}/api/market-activity/movers?limit=${limit}`);
  if (!response.ok) {
    throw new Error("Failed to fetch price movers");
  }
  return response.json();
}

export async function fetchClosingSoon(days = 7, limit = 20) {
  const response = await fetch(`${API_URL}/api/market-activity/closing-soon?days=${days}&limit=${limit}`);
  if (!response.ok) {
    throw new Error("Failed to fetch closing soon markets");
  }
  return response.json();
}

export async function searchMarkets(query: string, limit = 20) {
  const response = await fetch(`${API_URL}/api/market-activity/search?q=${encodeURIComponent(query)}&limit=${limit}`);
  if (!response.ok) {
    throw new Error("Failed to search markets");
  }
  return response.json();
}

// Arbitrage diagnostics
export async function fetchArbitrageDiagnostics() {
  const response = await fetch(`${API_URL}/api/arbitrage/diagnostics`);
  if (!response.ok) {
    throw new Error("Failed to fetch arbitrage diagnostics");
  }
  return response.json();
}
