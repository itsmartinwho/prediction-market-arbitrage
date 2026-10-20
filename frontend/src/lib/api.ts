// The dashboard calls the API on its own origin: on Vercel, /api/* is routed
// to the Python service; in `next dev`, next.config.js proxies /api/* to the
// local backend. Set NEXT_PUBLIC_API_URL only to call an API elsewhere.
import type { MarketListResponse } from "@/types/market";
import type { MarketSignal } from "@/types/news";
import type { OpportunitiesResponse, ApiStatus } from "@/types/opportunity";
import type { WhaleActivity } from "@/types/whale";

const API_BASE = (process.env.NEXT_PUBLIC_API_URL || "").replace(/\/$/, "");
const TIMEOUT_MS = 20_000;

export class ApiError extends Error {
  constructor(
    message: string,
    public status: number | null,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), TIMEOUT_MS);
  let response: Response;
  try {
    response = await fetch(`${API_BASE}${path}`, {
      ...init,
      headers: { Accept: "application/json", ...(init?.headers || {}) },
      signal: controller.signal,
    });
  } catch (err) {
    if ((err as Error)?.name === "AbortError") {
      throw new ApiError(`No answer after ${TIMEOUT_MS / 1000} seconds.`, null);
    }
    throw new ApiError("Can't reach the API.", null);
  } finally {
    clearTimeout(timer);
  }

  if (!response.ok) {
    let detail = "";
    try {
      const body = await response.json();
      detail = typeof body?.detail === "string" ? body.detail : "";
    } catch {
      // not JSON: keep the status alone
    }
    throw new ApiError(detail || `The API answered ${response.status}.`, response.status);
  }
  return response.json() as Promise<T>;
}

export function describeError(error: unknown): string {
  if (error instanceof ApiError) return error.message;
  if (error instanceof Error) return error.message;
  return "Something went wrong.";
}

export const fetchStatus = () => request<ApiStatus>("/api/status");

export const fetchOpportunities = () =>
  request<OpportunitiesResponse>("/api/arbitrage/opportunities");

export const fetchWhaleActivity = (limit = 30) =>
  request<WhaleActivity[]>(`/api/whales/activity?limit=${limit}`);

export const fetchSignals = (limit = 20) =>
  request<MarketSignal[]>(`/api/news?limit=${limit}`);

export const fetchHotMarkets = (limit = 20) =>
  request<MarketListResponse>(`/api/market-activity/hot?limit=${limit}`);

export const fetchPriceMovers = (limit = 20) =>
  request<MarketListResponse>(`/api/market-activity/movers?limit=${limit}`);

export const fetchClosingSoon = (days = 7, limit = 20) =>
  request<MarketListResponse>(
    `/api/market-activity/closing-soon?days=${days}&limit=${limit}`,
  );

export const searchMarkets = (query: string, limit = 20) =>
  request<MarketListResponse>(
    `/api/market-activity/search?q=${encodeURIComponent(query)}&limit=${limit}`,
  );
