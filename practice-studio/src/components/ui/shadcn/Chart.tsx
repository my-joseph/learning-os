"use client";

// Adapted from the shadcn/ui Chart registry item (MIT).
import React, { createContext, useContext, type ComponentProps, type CSSProperties } from "react";
import { ResponsiveContainer, Tooltip, type TooltipContentProps } from "recharts";
import { cn } from "@/lib/cn";

export type ChartConfig = Record<string, { label: React.ReactNode; color: string }>;

const ChartContext = createContext<ChartConfig | null>(null);

export function ChartContainer({
  config,
  children,
  className,
  ...props
}: ComponentProps<"div"> & {
  config: ChartConfig;
  children: ComponentProps<typeof ResponsiveContainer>["children"];
}) {
  const colors = Object.fromEntries(
    Object.entries(config).map(([key, item]) => [`--color-${key}`, item.color])
  ) as CSSProperties;

  return (
    <ChartContext.Provider value={config}>
      <div data-slot="chart" className={cn("flex justify-center text-xs", className)} style={colors} {...props}>
        <ResponsiveContainer>{children}</ResponsiveContainer>
      </div>
    </ChartContext.Provider>
  );
}

export const ChartTooltip = Tooltip;

export function ChartTooltipContent({
  active,
  payload,
}: Partial<TooltipContentProps>) {
  const config = useContext(ChartContext);
  if (!config) throw new Error("ChartTooltipContent requires a ChartContainer");
  if (!active || !payload?.length) return null;

  return (
    <div className="grid gap-space-1 rounded-lg border border-border bg-surface-raised px-space-3 py-space-1_5 shadow-lg">
      {payload.filter((item) => item.type !== "none").map((item) => {
        const key = String(item.name ?? item.dataKey ?? "value");
        const entry = config[key];
        return (
          <div key={key} className="flex items-center gap-space-2">
            <span
              aria-hidden="true"
              className="size-space-2 rounded-sm"
              style={{ backgroundColor: entry?.color ?? item.color }}
            />
            <span className="text-foreground-secondary">{entry?.label ?? item.name}</span>
            <span className="ml-auto font-semibold tabular-nums text-foreground">
              {item.value?.toLocaleString()}
            </span>
          </div>
        );
      })}
    </div>
  );
}
