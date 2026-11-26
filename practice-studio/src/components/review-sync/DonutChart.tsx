"use client";

import React from "react";
import { Pie, PieChart } from "recharts";
import { ChartContainer, ChartTooltip, ChartTooltipContent, type ChartConfig } from "@/components/ui/shadcn/Chart";
import { statusTone } from "@/lib/statusTone";
import { outcomeLabels, type OutcomeCounts } from "./reviewSyncOutcomes";

const chartConfig = {
  correct: { label: outcomeLabels.correct, color: statusTone.correct.chartColor },
  assisted: { label: outcomeLabels.assisted, color: statusTone.assisted.chartColor },
  wrong: { label: outcomeLabels.wrong, color: statusTone.wrong.chartColor },
  unattempted: { label: outcomeLabels.unattempted, color: statusTone.skipped.chartColor },
} satisfies ChartConfig;

/** Segments from shadcn's Pie Chart – Donut with Text example. The caller overlays the score. */
export function DonutChart({ counts }: { counts: OutcomeCounts }) {
  const segments = (Object.keys(chartConfig) as (keyof OutcomeCounts)[])
    .filter((name) => counts[name] > 0)
    .map((name) => ({
      name,
      count: counts[name],
      fill: name === "assisted" ? "transparent" : `var(--color-${name})`,
      stroke: name === "assisted" ? "var(--color-assisted)" : "none",
    }));

  return (
    <ChartContainer config={chartConfig} className="size-full" aria-hidden="true">
      <PieChart accessibilityLayer={false}>
        <ChartTooltip cursor={false} isAnimationActive={false} content={<ChartTooltipContent />} />
        <Pie
          data={segments}
          dataKey="count"
          nameKey="name"
          innerRadius="72%"
          outerRadius="96%"
          paddingAngle={2}
          startAngle={90}
          endAngle={-270}
          strokeWidth={2}
          rootTabIndex={-1}
          isAnimationActive={false}
        />
      </PieChart>
    </ChartContainer>
  );
}
