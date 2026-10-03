"use client";

import { useEffect, useRef } from "react";

/** Refresh the visible page on focus and periodically so other signed-in devices stay current. */
export function useLiveRefresh(refresh: () => void | Promise<void>, intervalMs = 12_000) {
  const refreshRef = useRef(refresh);

  useEffect(() => {
    refreshRef.current = refresh;
  }, [refresh]);

  useEffect(() => {
    let running = false;
    const run = () => {
      if (running || document.visibilityState !== "visible") return;
      running = true;
      void Promise.resolve(refreshRef.current()).catch(() => undefined).finally(() => {
        running = false;
      });
    };

    const timer = window.setInterval(run, intervalMs);
    window.addEventListener("focus", run);
    document.addEventListener("visibilitychange", run);
    run();
    return () => {
      window.clearInterval(timer);
      window.removeEventListener("focus", run);
      document.removeEventListener("visibilitychange", run);
    };
  }, [intervalMs]);
}
