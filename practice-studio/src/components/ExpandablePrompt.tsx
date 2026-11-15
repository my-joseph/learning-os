"use client";

import React, { useEffect, useRef, useState } from "react";
import { ChevronDown, ChevronUp } from "lucide-react";
import { FormattedText } from "./FormattedText";

interface ExpandablePromptProps {
  text: string;
}

export const ExpandablePrompt: React.FC<ExpandablePromptProps> = ({ text }) => {
  const [expanded, setExpanded] = useState(false);
  const [isOverflowing, setIsOverflowing] = useState(false);
  const contentRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setExpanded(false);
  }, [text]);

  useEffect(() => {
    const el = contentRef.current;
    if (!el || expanded) return;

    const checkOverflow = () => {
      // +2px tolerance avoids false positives from sub-pixel font/KaTeX line metrics
      setIsOverflowing(el.scrollHeight > el.clientHeight + 2);
    };

    checkOverflow();

    if (typeof ResizeObserver === "undefined") return;
    const observer = new ResizeObserver(checkOverflow);
    observer.observe(el);
    return () => observer.disconnect();
  }, [text, expanded]);

  return (
    <div>
      <div
        ref={contentRef}
        className={`text-xs text-slate-700 dark:text-slate-300 break-words overflow-hidden ${
          expanded ? "" : "line-clamp-2 max-h-[2.75rem]"
        }`}
      >
        <FormattedText text={text} />
      </div>

      {(isOverflowing || expanded) && (
        <button
          type="button"
          onClick={() => setExpanded((prev) => !prev)}
          aria-expanded={expanded}
          className="mt-1 inline-flex items-center gap-0.5 text-[11px] font-semibold text-indigo-600 dark:text-indigo-400 hover:text-indigo-500 dark:hover:text-indigo-300 hover:underline transition-colors"
        >
          <span>{expanded ? "See Less" : "See More"}</span>
          {expanded ? (
            <ChevronUp className="w-3 h-3" />
          ) : (
            <ChevronDown className="w-3 h-3" />
          )}
        </button>
      )}
    </div>
  );
};
