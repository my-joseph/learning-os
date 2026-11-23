"use client";

import { useState, useEffect, useCallback } from "react";
import { resolveTheme } from "@/lib/studioRules";

const STORAGE_KEY = "practice_studio_theme";
const SYNC_MIGRATION_KEY = "practice_studio_theme_sync_v1";

function applyDomTheme(next: "light" | "dark") {
  document.documentElement.classList.toggle("light", next === "light");
  document.documentElement.classList.toggle("dark", next === "dark");
}

/** Manage light/dark Studio theme state synced with prefers-color-scheme and localStorage. */
export function useTheme() {
  const [theme, setTheme] = useState<"light" | "dark">("dark");

  useEffect(() => {
    try {
      const mql = window.matchMedia("(prefers-color-scheme: dark)");
      let saved: string | null = null;
      try {
        if (!localStorage.getItem(SYNC_MIGRATION_KEY)) {
          localStorage.removeItem(STORAGE_KEY);
          localStorage.setItem(SYNC_MIGRATION_KEY, "1");
        }
        saved = localStorage.getItem(STORAGE_KEY);
      } catch {}

      const initial = resolveTheme(saved, mql.matches);
      applyDomTheme(initial);
      setTheme(initial);

      const handleMediaChange = (e: MediaQueryListEvent) => {
        const next = e.matches ? "dark" : "light";
        try {
          localStorage.removeItem(STORAGE_KEY);
        } catch {}
        applyDomTheme(next);
        setTheme(next);
      };

      mql.addEventListener("change", handleMediaChange);
      return () => mql.removeEventListener("change", handleMediaChange);
    } catch {}
  }, []);

  const handleToggleTheme = useCallback(() => {
    const next = theme === "light" ? "dark" : "light";
    setTheme(next);
    try {
      const systemTheme = window.matchMedia("(prefers-color-scheme: dark)").matches
        ? "dark"
        : "light";
      if (next === systemTheme) {
        localStorage.removeItem(STORAGE_KEY);
      } else {
        localStorage.setItem(STORAGE_KEY, next);
      }
    } catch {}
    applyDomTheme(next);
  }, [theme]);

  return { theme, handleToggleTheme };
}
