"use client";

import { useState, useEffect, useCallback } from "react";

/** Manage light/dark Studio theme state synced with documentElement and localStorage. */
export function useTheme() {
  const [theme, setTheme] = useState<"light" | "dark">("dark");

  useEffect(() => {
    try {
      const initial = document.documentElement.classList.contains("light") ? "light" : "dark";
      setTheme(initial);
    } catch {}
  }, []);

  const handleToggleTheme = useCallback(() => {
    const next = theme === "light" ? "dark" : "light";
    setTheme(next);
    try {
      localStorage.setItem("practice_studio_theme", next);
    } catch {}
    if (next === "light") {
      document.documentElement.classList.add("light");
      document.documentElement.classList.remove("dark");
    } else {
      document.documentElement.classList.add("dark");
      document.documentElement.classList.remove("light");
    }
  }, [theme]);

  return { theme, handleToggleTheme };
}
