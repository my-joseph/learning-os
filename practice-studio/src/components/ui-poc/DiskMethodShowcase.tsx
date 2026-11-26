"use client";

import React, { useCallback, useMemo, useState } from "react";
import { Minus, Plus } from "lucide-react";
import { FormattedText } from "@/components/FormattedText";
import { LazyDiskMethod } from "@/components/isometric/LazyDiskMethod";
import { PlaygroundReadout, PlaygroundShowcase, PlaygroundStat, PlaygroundStats } from "@/components/playground/PlaygroundShowcase";
import { Numeral } from "@/components/ui/Numeral";
import { Button } from "@/components/ui/shadcn/Button";
import { SegmentedChips } from "@/components/ui/shadcn/Tabs";
import {
  computePresetDiskMethod,
  DISK_PRESETS,
  type DiskPresetId,
  type SampleRule,
} from "@/lib/isometric/math/diskMethod";

const MIN_DISKS = 1;
const MAX_DISKS = 40;

const PRESET_OPTIONS = [
  { value: "sqrt", label: "√x on [0, 4]" },
  { value: "cone", label: "x on [0, 3]" },
  { value: "sine", label: "sin x on [0, π]" },
] as const;

const RULE_OPTIONS = [
  { value: "left", label: "Left" },
  { value: "midpoint", label: "Midpoint" },
  { value: "right", label: "Right" },
] as const;

const RULE_LABELS: Record<SampleRule, string> = {
  left: "Left endpoint",
  midpoint: "Midpoint",
  right: "Right endpoint",
};

function formatPercent(relativeError: number | null): string {
  if (relativeError === null) return "—";
  const pct = relativeError * 100;
  if (pct < 0.005) return "0.00%";
  return `${pct.toFixed(2)}%`;
}

export function DiskMethodShowcase() {
  const [preset, setPreset] = useState<DiskPresetId>("sqrt");
  const [n, setN] = useState<number>(8);
  const [rule, setRule] = useState<SampleRule>("right");
  const [inspectedIndex, setInspectedIndex] = useState<number | null>(null);
  const [caption, setCaption] = useState<string>(
    "n = 8 · right endpoint",
  );

  const presetMeta = DISK_PRESETS[preset];
  const result = useMemo(
    () => computePresetDiskMethod(preset, n, rule),
    [preset, n, rule],
  );

  const activeDisk =
    inspectedIndex !== null && result.disks[inspectedIndex]
      ? result.disks[inspectedIndex]
      : null;

  const handlePresetChange = useCallback((next: string) => {
    if (next === "sqrt" || next === "cone" || next === "sine") {
      setPreset(next);
      setInspectedIndex(null);
    }
  }, []);

  const handleRuleChange = useCallback((next: string) => {
    if (next === "left" || next === "midpoint" || next === "right") {
      setRule(next);
    }
  }, []);

  const handleChangeN = useCallback((nextN: number) => {
    const clamped = Math.max(MIN_DISKS, Math.min(MAX_DISKS, Math.round(nextN)));
    setN(clamped);
  }, []);

  const generalFormula =
    "$$V \\approx \\sum_{i=1}^{n} \\pi \\left[f(x_i^*)\\right]^2 \\Delta x \\longrightarrow \\pi \\int_{a}^{b} \\left[f(x)\\right]^2 \\, dx$$";

  const presetIntegralLatex =
    preset === "sqrt"
      ? "$\\pi \\int_{0}^{4} (\\sqrt{x})^2 \\, dx = 8\\pi$"
      : preset === "cone"
        ? "$\\pi \\int_{0}^{3} x^2 \\, dx = 9\\pi$"
        : "$\\pi \\int_{0}^{\\pi} \\sin^2 x \\, dx = \\frac{\\pi^2}{2}$";

  return (
    <PlaygroundShowcase
      title={<FormattedText text={`$${presetMeta.formulaLatex}$ on $${presetMeta.intervalLatex}$`} />}
      caption={<span data-testid="disk-caption">{caption}</span>}
      figure={
        <LazyDiskMethod
          preset={preset}
          n={n}
          rule={rule}
          onRead={setCaption}
          onInspectDisk={setInspectedIndex}
          onChangeN={handleChangeN}
        />
      }
      readout={
        <PlaygroundReadout action={
          <SegmentedChips
            label="Preset function"
            options={PRESET_OPTIONS}
            value={preset}
            onValueChange={handlePresetChange}
          />
        }>
          <div className="space-y-space-3 rounded-lg border border-border bg-surface-panel p-space-3">
            <div className="flex items-center justify-between gap-space-2">
              <label
                htmlFor="disk-count-slider"
                className="text-xs font-semibold text-foreground-secondary"
              >
                Disk count (<FormattedText text="$n$" />)
              </label>
              <div className="flex items-center gap-space-1_5">
                <Button
                  type="button"
                  variant="outline"
                  size="iconSm"
                  aria-label="Decrease disk count"
                  disabled={n <= MIN_DISKS}
                  onClick={() => handleChangeN(n - 1)}
                >
                  <Minus className="size-space-3_5" />
                </Button>
                <Numeral
                  variant="lg"
                  className="min-w-space-8 text-center text-base text-foreground"
                  data-testid="readout-n"
                >
                  {n}
                </Numeral>
                <Button
                  type="button"
                  variant="outline"
                  size="iconSm"
                  aria-label="Increase disk count"
                  disabled={n >= MAX_DISKS}
                  onClick={() => handleChangeN(n + 1)}
                >
                  <Plus className="size-space-3_5" />
                </Button>
              </div>
            </div>

            <input
              id="disk-count-slider"
              type="range"
              min={MIN_DISKS}
              max={MAX_DISKS}
              step={1}
              value={n}
              aria-label="Number of cylindrical disks"
              aria-valuetext={`${n} disks`}
              onChange={(e) => handleChangeN(Number(e.target.value))}
              className="min-h-touch w-full cursor-pointer accent-accent-primary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent focus-visible:ring-offset-2 focus-visible:ring-offset-background"
            />

            <div className="flex flex-wrap items-center justify-between gap-space-2 border-t border-border pt-space-2_5">
              <span className="text-xs font-semibold text-foreground-secondary">
                Sample point
              </span>
              <SegmentedChips
                label="Sample point rule"
                options={RULE_OPTIONS}
                value={rule}
                onValueChange={handleRuleChange}
              />
            </div>
          </div>
          <PlaygroundStats>
            <PlaygroundStat
              label={<>Slice width (<FormattedText text={"$\\Delta x$"} />)</>}
              value={result.dx.toFixed(3)}
              testId="readout-dx"
            />
            <PlaygroundStat
              label={<>Approx. volume (<FormattedText text={"$\\Sigma V_i$"} />)</>}
              value={result.approxVolume.toFixed(3)}
              testId="readout-approx"
            />
            <PlaygroundStat
              label="Exact volume"
              value={<FormattedText text={`$${presetMeta.exactLatex}$`} />}
              detail={<Numeral>({presetMeta.exactVolume.toFixed(3)})</Numeral>}
              testId="readout-exact"
            />
            <PlaygroundStat
              label={`Error (${RULE_LABELS[rule]})`}
              value={formatPercent(result.relativeError)}
              testId="readout-error"
            />
          </PlaygroundStats>
          <div
            className={
              activeDisk
                ? "rounded-lg border border-accent-field bg-accent-tint p-space-3 text-xs"
                : "rounded-lg border border-border bg-surface-panel p-space-3 text-xs"
            }
            data-testid="disk-inspector"
          >
            {activeDisk ? (
              <div className="space-y-space-1_5">
                <div className="flex items-center justify-between gap-space-2">
                  <span className="font-semibold text-accent">
                    Disk {activeDisk.index + 1} of {n}
                  </span>
                  <span className="font-mono text-foreground-secondary">
                    [{activeDisk.x0.toFixed(2)}, {activeDisk.x1.toFixed(2)}]
                  </span>
                </div>
                <div className="flex flex-wrap items-center justify-between gap-space-2 text-foreground">
                  <FormattedText
                    text={`$x_{${activeDisk.index + 1}}^* = ${activeDisk.x.toFixed(3)}$, $r = ${activeDisk.r.toFixed(3)}$`}
                  />
                </div>
                <div className="border-t border-border pt-space-1_5 text-foreground">
                  <FormattedText
                    text={`$V_{${activeDisk.index + 1}} = \\pi \\cdot (${activeDisk.r.toFixed(3)})^2 \\cdot ${activeDisk.dx.toFixed(3)} = ${activeDisk.volume.toFixed(3)}$`}
                  />
                </div>
              </div>
            ) : (
              <p className="text-foreground-secondary">
                Hover, click, or focus a disk with Left/Right arrows to inspect its individual slice volume{" "}
                <FormattedText text={"$\\pi [f(x_i^*)]^2 \\Delta x$"} />.
              </p>
            )}
          </div>

          <div
            className="rounded-lg border border-border bg-surface-panel p-space-3"
            data-testid="disk-formula"
          >
            <div className="overflow-x-auto text-xs text-foreground">
              <FormattedText text={generalFormula} density="compact" block />
            </div>
            <div className="mt-space-1 border-t border-border pt-space-2 text-center text-xs text-foreground-secondary">
              <FormattedText text={presetIntegralLatex} />
            </div>
          </div>
          <p className="text-xs text-foreground-secondary">
            Drag across the solid or use the slider to change the disk count. Tab to the figure and press Left or Right to inspect disks.
          </p>
        </PlaygroundReadout>
      }
    />
  );
}
