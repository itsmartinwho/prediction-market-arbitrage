"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useState } from "react";
import { ApiError } from "@/lib/api";

export function Providers({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 15_000,
            refetchInterval: 60_000,
            // One retry for a dropped connection or a 5xx; a 4xx will not get better.
            retry: (failures, error) =>
              failures < 1 && !(error instanceof ApiError && error.status !== null && error.status < 500),
            retryDelay: 1_500,
          },
        },
      }),
  );

  return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
}
