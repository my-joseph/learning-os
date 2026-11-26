export type SampleRule = "left" | "midpoint" | "right";
export type DiskPresetId = "sqrt" | "cone" | "sine";

export type DiskSlice = {
  /** Zero-based slice index (0 .. n - 1). */
  index: number;
  /** Left endpoint of subinterval [x0, x1]. */
  x0: number;
  /** Right endpoint of subinterval [x0, x1]. */
  x1: number;
  /** Chosen sample point x_i* in [x0, x1]. */
  x: number;
  /** Non-negative disk radius r = |f(x_i*)|. */
  r: number;
  /** Disk thickness Δx = (b - a) / n. */
  dx: number;
  /** Disk volume V_i = π * r^2 * Δx. */
  volume: number;
};

export type DiskMethodResult = {
  a: number;
  b: number;
  n: number;
  dx: number;
  rule: SampleRule;
  disks: DiskSlice[];
  approxVolume: number;
  exactVolume: number | null;
  absoluteError: number | null;
  relativeError: number | null;
};

export type DiskPreset = {
  id: DiskPresetId;
  label: string;
  description: string;
  formulaLatex: string;
  integrandLatex: string;
  intervalLatex: string;
  a: number;
  b: number;
  f: (x: number) => number;
  exactVolume: number;
  exactLatex: string;
  exactSymbol: string;
  maxRadius: number;
  ticks: ReadonlyArray<{ x: number; label: string }>;
};

export const DISK_PRESETS: Record<DiskPresetId, DiskPreset> = {
  sqrt: {
    id: "sqrt",
    label: "f(x) = √x",
    description: "Paraboloid on [0, 4]",
    formulaLatex: "f(x) = \\sqrt{x}",
    integrandLatex: "x",
    intervalLatex: "[0, 4]",
    a: 0,
    b: 4,
    f: (x) => Math.sqrt(Math.max(0, x)),
    exactVolume: 8 * Math.PI,
    exactLatex: "8\\pi",
    exactSymbol: "8π",
    maxRadius: 2,
    ticks: [
      { x: 0, label: "0" },
      { x: 1, label: "1" },
      { x: 2, label: "2" },
      { x: 3, label: "3" },
      { x: 4, label: "4" },
    ],
  },
  cone: {
    id: "cone",
    label: "f(x) = x",
    description: "Right circular cone on [0, 3]",
    formulaLatex: "f(x) = x",
    integrandLatex: "x^2",
    intervalLatex: "[0, 3]",
    a: 0,
    b: 3,
    f: (x) => x,
    exactVolume: 9 * Math.PI,
    exactLatex: "9\\pi",
    exactSymbol: "9π",
    maxRadius: 3,
    ticks: [
      { x: 0, label: "0" },
      { x: 1, label: "1" },
      { x: 2, label: "2" },
      { x: 3, label: "3" },
    ],
  },
  sine: {
    id: "sine",
    label: "f(x) = sin x",
    description: "Sine arch on [0, π]",
    formulaLatex: "f(x) = \\sin x",
    integrandLatex: "\\sin^2 x",
    intervalLatex: "[0, \\pi]",
    a: 0,
    b: Math.PI,
    f: (x) => Math.sin(x),
    exactVolume: (Math.PI * Math.PI) / 2,
    exactLatex: "\\frac{\\pi^2}{2}",
    exactSymbol: "π²/2",
    maxRadius: 1,
    ticks: [
      { x: 0, label: "0" },
      { x: Math.PI / 2, label: "π/2" },
      { x: Math.PI, label: "π" },
    ],
  },
};

export const DISK_PRESET_LIST: readonly DiskPreset[] = [
  DISK_PRESETS.sqrt,
  DISK_PRESETS.cone,
  DISK_PRESETS.sine,
];

const ZERO_EPS = 1e-12;

function sampleX(x0: number, x1: number, rule: SampleRule): number {
  if (rule === "left") return x0;
  if (rule === "right") return x1;
  return (x0 + x1) / 2;
}

/**
 * Pure Disk Method Riemann-sum computation for rotating y = f(x) around the
 * x-axis on [a, b] using n coaxial cylindrical disks of thickness Δx = (b - a)/n.
 */
export function computeDiskMethod(
  f: (x: number) => number,
  a: number,
  b: number,
  n: number,
  rule: SampleRule,
  exactVolume: number | null = null,
): DiskMethodResult {
  if (!Number.isFinite(a) || !Number.isFinite(b) || b <= a) {
    throw new RangeError(`Expected finite bounds with b > a, got [${a}, ${b}]`);
  }
  if (!Number.isInteger(n) || n < 1) {
    throw new RangeError(`Expected integer disk count n >= 1, got ${n}`);
  }

  const dx = (b - a) / n;
  const disks: DiskSlice[] = [];
  let approxVolume = 0;

  for (let index = 0; index < n; index++) {
    const x0 = a + index * dx;
    const x1 = index === n - 1 ? b : a + (index + 1) * dx;
    const x = sampleX(x0, x1, rule);
    const raw = f(x);
    const r = Number.isFinite(raw) && Math.abs(raw) >= ZERO_EPS ? Math.abs(raw) : 0;
    const volume = Math.PI * r * r * dx;
    approxVolume += volume;
    disks.push({ index, x0, x1, x, r, dx, volume });
  }

  let absoluteError: number | null = null;
  let relativeError: number | null = null;
  if (exactVolume !== null && Number.isFinite(exactVolume)) {
    const rawErr = Math.abs(approxVolume - exactVolume);
    absoluteError = rawErr < ZERO_EPS ? 0 : rawErr;
    relativeError = exactVolume > 0 ? absoluteError / exactVolume : null;
  }

  return {
    a,
    b,
    n,
    dx,
    rule,
    disks,
    approxVolume,
    exactVolume,
    absoluteError,
    relativeError,
  };
}

/** Computes the Disk Method approximation for one of the built-in presets. */
export function computePresetDiskMethod(
  presetId: DiskPresetId,
  n: number,
  rule: SampleRule,
): DiskMethodResult {
  const preset = DISK_PRESETS[presetId];
  return computeDiskMethod(preset.f, preset.a, preset.b, n, rule, preset.exactVolume);
}
