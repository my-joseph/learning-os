"use client";

import { useState, useEffect, useCallback } from "react";
import { resolveTheme } from "@/lib/studioRules";

const STORAGE_KEY = "practice_studio_theme";

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
      const saved = localStorage.getItem(STORAGE_KEY);
      const initial = resolveTheme(saved, mql.matches);
      applyDomTheme(initial);
      setTheme(initial);

      const handleMediaChange = (e: MediaQueryListEvent) => {
        try {
          const override = localStorage.getItem(STORAGE_KEY);
          const resolved = resolveTheme(override, e.matches);
          applyDomTheme(resolved);
          setTheme(resolved);
        } catch {}
      };

      mql.addEventListener("change", handleMediaChange);
      return () => mql.removeEventListener("change", handleMediaChange);
    } catch {}
  }, []);

  const handleToggleTheme = useCallback(() => {
    const next = theme === "light" ? "dark" : "light";
    setTheme(next);
    try {
      localStorage.setItem(STORAGE_KEY, next);
    } catch {}
    applyDomTheme(next);
  }, [theme]);

  return { theme, handleToggleTheme };
}
