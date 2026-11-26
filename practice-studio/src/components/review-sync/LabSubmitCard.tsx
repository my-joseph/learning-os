"use client";

import React from "react";
import { Check, Copy, Terminal } from "lucide-react";
import { Numeral } from "@/components/ui/Numeral";
import { CopyButton } from "@/components/ui/CopyButton";
import { Card } from "@/components/ui/shadcn/Card";

interface LabSubmitCardProps {
  labId: string;
  summary: { passed: number; awaitingReview: number; revise: number; notTried: number; total: number };
}

export function LabSubmitCard({ labId, summary }: LabSubmitCardProps) {
  const submitCommand = `cd labs/${labId} && npm run submit`;
  const { total, passed, awaitingReview, revise, notTried } = summary;

  return (
    <Card asChild className="shadow-none p-4 sm:p-6 space-y-4">
      <section
      id="review-sync-section"
      aria-labelledby="sync-card-heading"
    >
      <div className="space-y-1">
        <h2
          id="sync-card-heading"
          className="text-sm font-semibold text-zinc-900 dark:text-zinc-100"
        >
          Submit lab
        </h2>
        <p className="text-sm text-zinc-600 dark:text-zinc-300">
          <Numeral variant="lg" className="text-foreground">{passed}</Numeral>
          {" "}of{" "}
          <Numeral variant="lg" className="text-foreground">{total}</Numeral>{" "}
          milestones passed
          {awaitingReview > 0 && (
            <>
              {" · "}
              <span className="font-sans tabular-nums">{awaitingReview}</span>{" "}
              awaiting review
            </>
          )}
          {revise > 0 && (
            <>
              {" · "}
              <span className="font-sans tabular-nums">{revise}</span>{" "}
              needs revision
            </>
          )}
          {notTried > 0 && (
            <>
              {" · "}
              <span className="font-sans tabular-nums">{notTried}</span>{" "}
              not tried
            </>
          )}
        </p>
      </div>

      <div className="flex items-center gap-2.5 rounded-xl bg-surface-panel border border-zinc-200 dark:border-zinc-800 px-3.5 py-3 overflow-x-auto">
        <Terminal className="w-4 h-4 text-zinc-500 dark:text-zinc-400 shrink-0" aria-hidden="true" />
        <code className="font-mono text-xs text-zinc-900 dark:text-zinc-100 whitespace-nowrap">
          {submitCommand}
        </code>
      </div>

      <div className="flex flex-col sm:flex-row sm:items-center gap-2.5">
        <CopyButton
          text={submitCommand}
          className="w-full sm:w-auto inline-flex items-center justify-center gap-2 min-h-[44px] sm:h-10 px-4 rounded-xl bg-indigo-600 hover:bg-indigo-700 dark:bg-indigo-600 dark:hover:bg-indigo-700 text-white text-sm font-semibold transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-600 dark:focus-visible:ring-indigo-400 shrink-0"
          timeoutMs={1500}
          copiedContent={
            <>
              <Check className="w-4 h-4" aria-hidden="true" />
              <span>Copied submit command</span>
            </>
          }
        >
          <>
            <Copy className="w-4 h-4" aria-hidden="true" />
            <span>Copy submit command</span>
          </>
        </CopyButton>

        <p className="text-xs text-zinc-500 dark:text-zinc-400 leading-relaxed">
          Runs every test (including hidden ones) and records the result in Notion.
        </p>
      </div>
      </section>
    </Card>
  );
}
