"use client";

import { ReactNode, useEffect, useState } from "react";
import { describeError } from "@/lib/api";

/** Waiting on the API. After a few seconds it says how long it has been. */
export function LoadingState({ what }: { what: string }) {
  const [seconds, setSeconds] = useState(0);
  useEffect(() => {
    const started = Date.now();
    const id = setInterval(() => setSeconds(Math.floor((Date.now() - started) / 1000)), 1000);
    return () => clearInterval(id);
  }, []);

  return (
    <div className="py-12 text-center" role="status" aria-live="polite">
      <div className="inline-flex items-center gap-2 text-sm text-gray-300">
        <span className="h-2 w-2 animate-pulse rounded-full bg-neon-cyan" aria-hidden />
        Fetching {what} from Polymarket…
      </div>
      <p className="mt-2 text-xs text-gray-500">
        {seconds < 4
          ? "The first request after a quiet spell takes a few seconds."
          : `Still waiting (${seconds}s). If Polymarket doesn't answer, this says so.`}
      </p>
    </div>
  );
}

/** The request failed and there is nothing to show. */
export function ErrorState({
  what,
  error,
  onRetry,
}: {
  what: string;
  error: unknown;
  onRetry: () => void;
}) {
  return (
    <div className="py-12 text-center" role="alert">
      <p className="text-sm text-neon-red">Couldn&apos;t load {what}.</p>
      <p className="mt-1 text-xs text-gray-500">{describeError(error)}</p>
      <button onClick={onRetry} className="cyber-button mt-4 text-xs">
        Try again
      </button>
    </div>
  );
}

/** The request worked and the answer is genuinely empty. */
export function EmptyState({ title, hint }: { title: string; hint?: ReactNode }) {
  return (
    <div className="py-12 text-center">
      <p className="text-sm text-gray-300">{title}</p>
      {hint && <p className="mx-auto mt-2 max-w-md text-xs text-gray-500">{hint}</p>}
    </div>
  );
}

/** Data is on screen but the latest refresh failed. */
export function StaleNotice({ error }: { error: unknown }) {
  return (
    <p className="mb-3 rounded border border-neon-yellow/30 bg-neon-yellow/5 px-3 py-2 text-xs text-neon-yellow">
      The last refresh failed ({describeError(error)}). Showing the previous data.
    </p>
  );
}
