"use client";

import * as React from "react";
import {
  ResponsiveContainer,
  Tooltip,
  type TooltipProps,
} from "recharts";
import type { NameType, ValueType } from "recharts/types/component/DefaultTooltipContent";

export type ChartConfig = Record<
  string,
  {
    label?: React.ReactNode;
    color?: string;
  }
>;

interface ChartContainerProps extends React.HTMLAttributes<HTMLDivElement> {
  config: ChartConfig;
  aspectRatio?: number;
  initialDimension?: { width: number; height: number };
  children: React.ReactElement;
}

export const ChartContainer = React.forwardRef<HTMLDivElement, ChartContainerProps>(
  (
    {
      id,
      className,
      config,
      aspectRatio = 2,
      initialDimension = { width: 320, height: 160 },
      children,
      style,
      ...props
    },
    ref
  ) => {
    const chartId = React.useId().replace(/:/g, "");
    const scopedId = id ?? `chart-${chartId}`;
    const variables = Object.entries(config).flatMap(([key, entry]) =>
      entry.color ? [`--color-${key}: ${entry.color};`] : []
    );

    return (
      <div
        ref={ref}
        data-chart={scopedId}
        className={className}
        style={{ aspectRatio, ...style }}
        {...props}
      >
        <style>{`[data-chart="${scopedId}"] { ${variables.join(" ")} }`}</style>
        <ResponsiveContainer
          width="100%"
          height="100%"
          initialDimension={initialDimension}
        >
          {children}
        </ResponsiveContainer>
      </div>
    );
  }
);
ChartContainer.displayName = "ChartContainer";

export const ChartTooltip = Tooltip;

type ChartTooltipContentProps = TooltipProps<ValueType, NameType> & {
  hideLabel?: boolean;
  hideIndicator?: boolean;
  indicatorColor?: string;
  formatter?: TooltipProps<ValueType, NameType>["formatter"];
};

export const ChartTooltipContent: React.FC<ChartTooltipContentProps> = ({
  active,
  payload,
  label,
  hideLabel = false,
  hideIndicator = false,
  indicatorColor,
  formatter,
}) => {
  if (!active || !payload?.length) return null;

  const item = payload[0];
  const displayValue = formatter && item.value !== undefined
    ? formatter(item.value, item.name ?? "Score", item, 0, payload)
    : item.value;

  return (
    <div className="rounded-lg border border-zinc-200 bg-white px-3 py-2 text-xs shadow-md dark:border-zinc-700 dark:bg-zinc-900">
      {!hideLabel && (
        <p className="mb-1 font-semibold text-zinc-800 dark:text-zinc-100">
          {String(label ?? item.payload?.label ?? item.name ?? "Score")}
        </p>
      )}
      <div className="flex items-center gap-2 text-zinc-600 dark:text-zinc-300">
        {!hideIndicator && (
          <span
            aria-hidden="true"
            className="h-2 w-2 rounded-sm"
            style={{ backgroundColor: indicatorColor ?? String(item.color ?? "rgb(var(--accent))") }}
          />
        )}
        <span>{displayValue === undefined || displayValue === null ? "0" : String(displayValue)}</span>
      </div>
    </div>
  );
};
