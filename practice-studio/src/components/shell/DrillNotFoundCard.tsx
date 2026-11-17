"use client";

import React from "react";
import Link from "next/link";
import { ArrowLeft } from "lucide-react";

interface DrillNotFoundCardProps {
  drillId: string;
}

/** Calm empty/not-found card shown when a requested drill ID does not exist. */
export const DrillNotFoundCard: React.FC<DrillNotFoundCardProps> = ({ drillId }) => {
  return (
    <div className="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-2xl p-8 text-center space-y-4">
      <div className="space-y-1.5">
        <h2 className="text-lg font-semibold text-zinc-900 dark:text-zinc-100">
          Drill not found
        </h2>
        <p className="text-sm text-zinc-500 dark:text-zinc-400">
          We could not find a practice drill matching{" "}
          <code className="font-mono text-zinc-800 dark:text-zinc-200 bg-zinc-100 dark:bg-zinc-800 px-1.5 py-0.5 rounded">
            {drillId}
          </code>
          .
        </p>
      </div>
      <div>
        <Link
          href="/"
          className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-medium transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Studio</span>
        </Link>
      </div>
    </div>
  );
};
