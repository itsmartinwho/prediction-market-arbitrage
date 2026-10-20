"use client";

import { useQuery } from "@tanstack/react-query";
import { fetchOpportunities, fetchStatus } from "@/lib/api";

// Shared by the header and the Arbitrage tab, so both read one request.

export function useStatus() {
  return useQuery({
    queryKey: ["status"],
    queryFn: fetchStatus,
    refetchInterval: 60_000,
  });
}

export function useOpportunities() {
  return useQuery({
    queryKey: ["opportunities"],
    queryFn: fetchOpportunities,
    refetchInterval: 30_000,
  });
}
