"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";

/**
 * Periodically refreshes the page so Server Components re-fetch data.
 * Useful for pages that display data updated by external pipelines
 * (e.g. tickets arriving via webhook).
 */
export default function AutoRefresh({ intervalMs = 30000 }: { intervalMs?: number }) {
  const router = useRouter();

  useEffect(() => {
    const id = setInterval(() => router.refresh(), intervalMs);
    return () => clearInterval(id);
  }, [router, intervalMs]);

  return null;
}