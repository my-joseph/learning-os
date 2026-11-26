"use client";

import * as React from "react";
import { frame } from "@/lib/isometric/entity";
import { clamp, type Vec3 } from "@/lib/isometric/iso";
import { cylinder, zToX } from "@/lib/isometric/mesh";
import {
  computePresetDiskMethod,
  DISK_PRESETS,
  type DiskPresetId,
  type DiskSlice,
  type SampleRule,
} from "@/lib/isometric/math/diskMethod";
import { reducedMotion, spring, step, type Spring } from "@/lib/isometric/motion";
import { label, scene, type Item } from "@/lib/isometric/scene";
import { bag, el, loop, pointer } from "@/lib/isometric/stage";
import { inject } from "@/lib/isometric/styles";

export type DiskMethodProps = {
  /** Which preset curve y = f(x) to revolve around the x-axis. */
  preset?: DiskPresetId;
  /** Number of cylindrical disks (1–40). */
  n?: number;
  /** Riemann sample point rule within each subinterval. */
  rule?: SampleRule;
  /** Optional controlled highlighted disk index (0 .. n - 1). */
  highlightedDisk?: number | null;
  /** Accessible name for the interactive figure. */
  label?: string;
  /** Theme override ("auto" follows Practice Studio tokens). */
  theme?: "auto" | "light" | "dark";
  /** Called whenever the figure's live caption changes. */
  onRead?: (text: string) => void;
  /** Called when the user hovers, focuses, or pins a disk (or clears inspection). */
  onInspectDisk?: (diskIndex: number | null) => void;
  /** Called when the user drags horizontally or uses Up/Down arrows on the figure to change n. */
  onChangeN?: (nextN: number) => void;
  /** Called when a disk is clicked or activated with Enter/Space. */
  onActivate?: (part: string) => void;
  className?: string;
};

const MIN_N = 1;
const MAX_N = 40;
const AXIS_LEN = 74;
const X_START = -AXIS_LEN / 2;
const X_END = AXIS_LEN / 2;
const MAX_R = 23;
const CURVE_SAMPLES = 64;
const ZERO_R_THRESHOLD = 0.45;
const ZERO_HUB_R = 1.1;

const VIEW_FIT: Vec3[] = [
  [X_START - 9, -MAX_R - 4, -MAX_R - 9],
  [X_END + 11, MAX_R + 4, -MAX_R - 9],
  [X_START - 9, -MAX_R - 4, MAX_R + 7],
  [X_END + 11, MAX_R + 4, MAX_R + 7],
];

const useIsoLayoutEffect =
  typeof window === "undefined" ? React.useEffect : React.useLayoutEffect;

function parseDiskIndex(part: string | null): number | null {
  if (!part || !part.startsWith("disk-")) return null;
  const idx = Number(part.slice(5));
  return Number.isInteger(idx) && idx >= 0 ? idx : null;
}

function formatDiskCaption(slice: DiskSlice, total: number): string {
  return `disk ${slice.index + 1}/${total} · x* = ${slice.x.toFixed(2)} · r = ${slice.r.toFixed(2)} · V = ${slice.volume.toFixed(3)}`;
}

function formatRestCaption(presetId: DiskPresetId, n: number, rule: SampleRule, approx: number): string {
  const preset = DISK_PRESETS[presetId];
  return `n = ${n} · ${rule} · ΣV = ${approx.toFixed(3)} (exact ${preset.exactSymbol})`;
}

/**
 * DiskMethod — interactive isometric visualization of the calculus Disk Method
 * for rotating y = f(x) around the x-axis. Built on the MIT Isometric engine.
 */
export const DiskMethod = React.forwardRef<HTMLDivElement, DiskMethodProps>(
  function DiskMethod(
    {
      preset = "sqrt",
      n: rawN = 8,
      rule = "midpoint",
      highlightedDisk = null,
      label: ariaLabel,
      theme = "auto",
      onRead,
      onInspectDisk,
      onChangeN,
      onActivate,
      className,
    },
    ref,
  ) {
    const n = clamp(Math.round(rawN), MIN_N, MAX_N);
    const hostRef = React.useRef<HTMLDivElement | null>(null);
    const liveRef = React.useRef<HTMLSpanElement | null>(null);

    const callbacksRef = React.useRef({
      onRead,
      onInspectDisk,
      onChangeN,
      onActivate,
    });
    useIsoLayoutEffect(() => {
      callbacksRef.current = { onRead, onInspectDisk, onChangeN, onActivate };
    });

    const controllerRef = React.useRef<{
      sync: (
        nextPreset: DiskPresetId,
        nextN: number,
        nextRule: SampleRule,
        nextExternalHighlight: number | null,
      ) => void;
    } | null>(null);

    const initialRef = React.useRef({ preset, n, rule, highlightedDisk });

    useIsoLayoutEffect(() => {
      const stage = hostRef.current!;
      const root = stage.getRootNode();
      inject(
        root.nodeType === 9 || "host" in root
          ? (root as Document | ShadowRoot)
          : document,
      );

      const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
      svg.setAttribute("viewBox", "0 0 400 320");
      svg.setAttribute("aria-hidden", "true");
      stage.prepend(svg);

      const b = bag();
      const cam = frame({ az: -22, k: 0.48, fit: VIEW_FIT, zoom: 1.04, at: [200, 160] });
      const sc = scene(el("g", null, svg));

      let curPreset: DiskPresetId = initialRef.current.preset;
      let curN = initialRef.current.n;
      let curRule: SampleRule = initialRef.current.rule;
      let externalHighlight: number | null = initialRef.current.highlightedDisk;
      let result = computePresetDiskMethod(curPreset, curN, curRule);

      const radii: Spring[] = Array.from({ length: MAX_N }, () =>
        spring(0, 180, 22, 0.015),
      );
      const settle: Spring = spring(1, 180, 22, 0.005);

      const toWorldX = (x: number, a: number, bb: number) =>
        X_START + ((x - a) / (bb - a)) * AXIS_LEN;
      const toWorldR = (r: number, maxRadius: number) =>
        (r / maxRadius) * MAX_R;

      const seedImmediate = () => {
        const p = DISK_PRESETS[curPreset];
        for (let i = 0; i < MAX_N; i++) {
          const target = i < result.disks.length ? toWorldR(result.disks[i].r, p.maxRadius) : 0;
          radii[i].x = radii[i].to = target;
          radii[i].v = 0;
        }
        settle.x = settle.to = 1;
        settle.v = 0;
      };
      seedImmediate();

      let hoverIndex: number | null = null;
      let focusIndex: number | null = null;
      let pinnedIndex: number | null = null;
      let lastCaption = "";

      const activeDiskIndex = (): number | null => {
        const candidate = hoverIndex ?? focusIndex ?? pinnedIndex ?? externalHighlight;
        if (candidate === null || candidate < 0 || candidate >= curN) return null;
        return candidate;
      };

      const writeRead = (text: string) => {
        if (text === lastCaption) return;
        lastCaption = text;
        if (liveRef.current) liveRef.current.textContent = text;
        callbacksRef.current.onRead?.(text);
      };

      const emitInspect = () => {
        const idx = activeDiskIndex();
        callbacksRef.current.onInspectDisk?.(idx);
        if (idx !== null && result.disks[idx]) {
          writeRead(formatDiskCaption(result.disks[idx], curN));
        } else {
          writeRead(formatRestCaption(curPreset, curN, curRule, result.approxVolume));
        }
      };

      const renderScene = () => {
        const p = DISK_PRESETS[curPreset];
        const items: Item[] = [];
        const active = activeDiskIndex();
        const sides = curN <= 16 ? 28 : 20;
        const axisY = 0;
        const rulerZ = -MAX_R - 4;
        const tickZ = rulerZ - 1.8;
        const labelZ = rulerZ - 6.0;

        // Back-right x-axis extension and arrow
        items.push({
          pts: [
            [X_END, axisY, 0],
            [X_END + 9, axisY, 0],
          ],
          cls: "mid",
        });
        items.push({
          pts: [
            [X_END + 6.5, axisY, 1.3],
            [X_END + 9, axisY, 0],
            [X_END + 6.5, axisY, -1.3],
          ],
          cls: "mid",
        });
        items.push(
          label("x", [X_END + 10.2, axisY, -1.2], [1, 0, 0], [0, 0, 1], 3.4, {
            cls: "hi",
            anchor: "start",
          }),
        );

        // Front-left x-axis extension and subtle vertical y-axis stub at x = a
        items.push({
          pts: [
            [X_START - 7, axisY, 0],
            [X_START, axisY, 0],
          ],
          cls: "mid",
        });
        items.push({
          pts: [
            [X_START, axisY, 0],
            [X_START, axisY, MAX_R + 5],
          ],
          cls: "lo",
        });
        items.push({
          pts: [
            [X_START - 1.1, axisY, MAX_R + 2.8],
            [X_START, axisY, MAX_R + 5],
            [X_START + 1.1, axisY, MAX_R + 2.8],
          ],
          cls: "lo",
        });
        items.push(
          label("y", [X_START - 1.4, axisY, MAX_R + 5.8], [1, 0, 0], [0, 0, 1], 3.2, {
            cls: "mid",
            anchor: "end",
          }),
        );

        // Bottom x-axis ruler with ticks and numeric labels
        items.push({
          pts: [
            [X_START, axisY, rulerZ],
            [X_END, axisY, rulerZ],
          ],
          cls: "lo",
        });
        for (const tick of p.ticks) {
          const wx = toWorldX(tick.x, p.a, p.b);
          items.push({
            pts: [
              [wx, axisY, rulerZ + 1.2],
              [wx, axisY, tickZ],
            ],
            cls: "mid",
          });
          items.push(
            label(tick.label, [wx, axisY, labelZ], [1, 0, 0], [0, 0, 1], 3.1, {
              cls: "mid",
              anchor: "middle",
            }),
          );
        }

        // n coaxial cylindrical disks along the x-axis
        for (let i = 0; i < result.disks.length; i++) {
          const disk = result.disks[i];
          const wx0 = toWorldX(disk.x0, p.a, p.b);
          const wx1 = toWorldX(disk.x1, p.a, p.b);
          const thickness = Math.max(0.25, wx1 - wx0);
          const animatedR = Math.max(0, radii[i].x);
          const isActive = active === i;
          const part = `disk-${i}`;

          if (animatedR >= ZERO_R_THRESHOLD) {
            const mesh = zToX(cylinder(0, 0, wx0, animatedR, thickness, sides));
            items.push({
              mesh,
              smooth: true,
              shade: true,
              part,
              cls: isActive ? "accent glow" : "",
            });
          } else {
            const hub = zToX(cylinder(0, 0, wx0, ZERO_HUB_R, thickness, 16));
            items.push({
              mesh: hub,
              smooth: true,
              part,
              cls: isActive ? "accent glow" : "lo",
            });
          }
        }

        // Faint outline of the exact curve profile y = f(x) on top
        const curvePts: Vec3[] = [];
        for (let k = 0; k <= CURVE_SAMPLES; k++) {
          const t = k / CURVE_SAMPLES;
          const xVal = p.a + t * (p.b - p.a);
          const rVal = toWorldR(Math.max(0, p.f(xVal)), p.maxRadius);
          curvePts.push([toWorldX(xVal, p.a, p.b), axisY, rVal]);
        }
        items.push({
          pts: curvePts,
          cls: "edge dash",
          layer: 1,
        });

        // Radius & sample-point guide on the highlighted disk
        if (active !== null && result.disks[active]) {
          const disk = result.disks[active];
          const wxSample = toWorldX(disk.x, p.a, p.b);
          const rWorld = Math.max(0, radii[active].x);
          if (rWorld >= ZERO_R_THRESHOLD) {
            items.push({
              pts: [
                [wxSample, axisY, 0],
                [wxSample, axisY, rWorld],
              ],
              cls: "accent",
              layer: 2,
            });
          }
          const markerHalf = 1.25;
          items.push({
            pts: [
              [wxSample - markerHalf, axisY, rWorld],
              [wxSample + markerHalf, axisY, rWorld],
            ],
            cls: "accent",
            layer: 2,
          });
        }

        sc.render(cam, items);
      };

      const L = loop(stage, (dt) => {
        let moving = step(settle, dt);
        for (let i = 0; i < curN; i++) {
          if (step(radii[i], dt)) moving = true;
        }
        renderScene();
        return moving;
      });
      b.add(L.stop);

      writeRead(formatRestCaption(curPreset, curN, curRule, result.approxVolume));

      const setTargets = (prevN: number, prevPreset: DiskPresetId, prevRadiiSnapshot: number[]) => {
        const p = DISK_PRESETS[curPreset];
        const instant = reducedMotion();
        const samePresetAndN = prevN === curN && prevPreset === curPreset;

        for (let i = 0; i < MAX_N; i++) {
          const target =
            i < result.disks.length ? toWorldR(result.disks[i].r, p.maxRadius) : 0;
          if (instant) {
            radii[i].x = radii[i].to = target;
            radii[i].v = 0;
          } else if (i < result.disks.length) {
            if (!samePresetAndN && prevN !== curN) {
              // Seed from the nearest previous disk's radius scaled slightly down so spring settle reads clearly
              const mappedIdx = clamp(
                Math.floor(((i + 0.5) / curN) * prevN),
                0,
                Math.max(0, prevN - 1),
              );
              const seed = prevRadiiSnapshot[mappedIdx] ?? target * 0.72;
              radii[i].x = seed * 0.82;
              radii[i].v = 0;
            }
            radii[i].to = target;
          } else {
            radii[i].x = radii[i].to = 0;
            radii[i].v = 0;
          }
        }
        if (instant) {
          settle.x = settle.to = 1;
          settle.v = 0;
        } else {
          settle.x = 0;
          settle.to = 1;
          settle.v = 0;
        }
      };

      controllerRef.current = {
        sync(nextPreset, nextN, nextRule, nextExternalHighlight) {
          const prevPreset = curPreset;
          const prevN = curN;
          const prevRule = curRule;
          const prevExternal = externalHighlight;
          externalHighlight = nextExternalHighlight;

          if (
            nextPreset === prevPreset &&
            nextN === prevN &&
            nextRule === prevRule
          ) {
            if (nextExternalHighlight !== prevExternal) {
              L.wake();
            }
            return;
          }

          const snapshot = radii.slice(0, prevN).map((sp) => sp.x);
          curPreset = nextPreset;
          curN = nextN;
          curRule = nextRule;
          result = computePresetDiskMethod(curPreset, curN, curRule);

          if (hoverIndex !== null && hoverIndex >= curN) hoverIndex = curN - 1;
          if (focusIndex !== null && focusIndex >= curN) focusIndex = curN - 1;
          if (pinnedIndex !== null && pinnedIndex >= curN) pinnedIndex = curN - 1;

          setTargets(prevN, prevPreset, snapshot);
          emitInspect();
          L.wake();
        },
      };

      let dragStartX: number | null = null;
      let dragStartN = curN;
      let dragged = false;

      b.add(
        pointer(stage, {
          move(pt) {
            if (dragStartX !== null) {
              const dxScreen = pt[0] - dragStartX;
              if (Math.abs(dxScreen) > 5) dragged = true;
              if (dragged) {
                const deltaN = Math.round(dxScreen / 7);
                const nextN = clamp(dragStartN + deltaN, MIN_N, MAX_N);
                if (nextN !== curN) {
                  callbacksRef.current.onChangeN?.(nextN);
                }
                return;
              }
            }
            const nextHover = parseDiskIndex(sc.pick(pt));
            if (nextHover !== hoverIndex) {
              hoverIndex = nextHover;
              stage.style.cursor = nextHover !== null ? "pointer" : "ew-resize";
              emitInspect();
              L.wake();
            }
          },
          down(pt) {
            dragStartX = pt[0];
            dragStartN = curN;
            dragged = false;
            const hit = parseDiskIndex(sc.pick(pt));
            if (hit !== hoverIndex) {
              hoverIndex = hit;
              emitInspect();
              L.wake();
            }
          },
          up(pt) {
            const wasDrag = dragged;
            dragStartX = null;
            dragged = false;
            if (!wasDrag) {
              const hit = parseDiskIndex(sc.pick(pt));
              if (hit !== null) {
                pinnedIndex = pinnedIndex === hit ? null : hit;
                callbacksRef.current.onActivate?.(`disk-${hit}`);
                emitInspect();
                L.wake();
              } else if (pinnedIndex !== null) {
                pinnedIndex = null;
                emitInspect();
                L.wake();
              }
            }
          },
          leave() {
            dragStartX = null;
            dragged = false;
            if (hoverIndex !== null) {
              hoverIndex = null;
              stage.style.cursor = "";
              emitInspect();
              L.wake();
            }
          },
        }),
      );

      const onKeyDown = (e: KeyboardEvent) => {
        if (e.key === "ArrowRight") {
          e.preventDefault();
          focusIndex = focusIndex === null ? 0 : (focusIndex + 1) % curN;
          emitInspect();
          L.wake();
          return;
        }
        if (e.key === "ArrowLeft") {
          e.preventDefault();
          focusIndex = focusIndex === null ? curN - 1 : (focusIndex - 1 + curN) % curN;
          emitInspect();
          L.wake();
          return;
        }
        if (e.key === "ArrowUp" || e.key === "+" || e.key === "=") {
          e.preventDefault();
          const nextN = clamp(curN + 1, MIN_N, MAX_N);
          if (nextN !== curN) callbacksRef.current.onChangeN?.(nextN);
          return;
        }
        if (e.key === "ArrowDown" || e.key === "-") {
          e.preventDefault();
          const nextN = clamp(curN - 1, MIN_N, MAX_N);
          if (nextN !== curN) callbacksRef.current.onChangeN?.(nextN);
          return;
        }
        if ((e.key === "Enter" || e.key === " ") && focusIndex !== null) {
          e.preventDefault();
          pinnedIndex = pinnedIndex === focusIndex ? null : focusIndex;
          callbacksRef.current.onActivate?.(`disk-${focusIndex}`);
          emitInspect();
          L.wake();
          return;
        }
        if (e.key === "Escape") {
          focusIndex = null;
          pinnedIndex = null;
          emitInspect();
          L.wake();
        }
      };

      const onBlur = () => {
        if (focusIndex !== null) {
          focusIndex = null;
          emitInspect();
          L.wake();
        }
      };

      stage.addEventListener("keydown", onKeyDown);
      stage.addEventListener("blur", onBlur);
      b.add(() => {
        stage.removeEventListener("keydown", onKeyDown);
        stage.removeEventListener("blur", onBlur);
      });
      b.add(() => svg.replaceChildren());

      return () => {
        controllerRef.current = null;
        b.dispose();
        svg.remove();
      };
    }, []);

    useIsoLayoutEffect(() => {
      controllerRef.current?.sync(preset, n, rule, highlightedDisk);
    }, [preset, n, rule, highlightedDisk]);

    const setRef = React.useCallback(
      (node: HTMLDivElement | null) => {
        hostRef.current = node;
        if (typeof ref === "function") ref(node);
        else if (ref) {
          (ref as React.MutableRefObject<HTMLDivElement | null>).current = node;
        }
      },
      [ref],
    );

    const presetMeta = DISK_PRESETS[preset];
    const computedLabel =
      ariaLabel ??
      `Isometric Disk Method solid for ${presetMeta.label} on ${presetMeta.description.split(" on ")[1] ?? ""} with ${n} ${rule}-endpoint disks. Use Left and Right arrows to inspect disks, Up and Down arrows or drag horizontally to adjust disk count.`;

    return (
      <div
        ref={setRef}
        data-iso="disk-method"
        data-iso-theme={theme === "auto" ? undefined : theme}
        role="group"
        tabIndex={0}
        aria-label={computedLabel}
        className={`iso-figure-box w-full ${className ?? ""}`.trim()}
      >
        <span data-iso-live="" aria-live="polite" ref={liveRef} />
      </div>
    );
  },
);

DiskMethod.displayName = "DiskMethod";
