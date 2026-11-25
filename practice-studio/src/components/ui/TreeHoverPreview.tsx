"use client";

import * as React from "react";
import { createPortal } from "react-dom";
import { AnimatePresence, m } from "motion/react";
import { popoverFromLeft, quick } from "@/lib/motion";

/*
 * One shared hover card for the sidebar tree (learner 2026-11-26).
 * The first card waits OPEN_DELAY_MS; while it is showing, moving to another row
 * moves the SAME card to that row quickly (no content fade), so sweeping down the list is
 * smooth and two cards never overlap. Desktop pointer only.
 */
const OPEN_DELAY_MS = 500;
const CLOSE_DELAY_MS = 120;
const SIDE_OFFSET_PX = 22;

interface PreviewTarget {
  key: string;
  preview: React.ReactNode;
  top: number;
  left: number;
}

interface PreviewState {
  target: PreviewTarget | null;
  visible: boolean;
}

let state: PreviewState = { target: null, visible: false };
let openTimer: ReturnType<typeof setTimeout> | undefined;
let closeTimer: ReturnType<typeof setTimeout> | undefined;
const listeners = new Set<() => void>();

function setState(next: PreviewState) {
  state = next;
  listeners.forEach((listener) => listener());
}

function clearTimers() {
  clearTimeout(openTimer);
  clearTimeout(closeTimer);
}

function hasDesktopPointer() {
  return typeof window !== "undefined" && window.matchMedia?.("(hover: hover) and (pointer: fine)").matches;
}

function targetFor(el: HTMLElement, key: string, preview: React.ReactNode): PreviewTarget {
  const rect = el.getBoundingClientRect();
  return { key, preview, top: rect.top, left: rect.right + SIDE_OFFSET_PX };
}

function showTreePreview(el: HTMLElement, key: string, preview: React.ReactNode) {
  if (!hasDesktopPointer()) return;
  clearTimers();
  if (state.visible) {
    setState({ target: targetFor(el, key, preview), visible: true });
    return;
  }
  openTimer = setTimeout(() => setState({ target: targetFor(el, key, preview), visible: true }), OPEN_DELAY_MS);
}

function leaveTreePreview() {
  clearTimeout(openTimer);
  clearTimeout(closeTimer);
  if (!state.visible) return;
  closeTimer = setTimeout(() => setState({ ...state, visible: false }), CLOSE_DELAY_MS);
}

function hideTreePreview() {
  clearTimers();
  if (state.visible) setState({ ...state, visible: false });
}

function subscribe(listener: () => void) {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

/** Row handlers for a tree row that has a preview. */
export function useTreePreviewTrigger(key: string, preview: React.ReactNode | undefined, disabled = false) {
  const previewRef = React.useRef(preview);
  previewRef.current = preview;
  React.useEffect(() => {
    if (disabled && state.target?.key === key) hideTreePreview();
  }, [disabled, key]);
  if (!preview) return {};
  return {
    onPointerEnter: (event: React.PointerEvent<HTMLElement>) => {
      if (disabled || event.pointerType === "touch") return;
      showTreePreview(event.currentTarget, key, previewRef.current);
    },
    onPointerLeave: () => leaveTreePreview(),
  };
}

/** Render once per sidebar. */
export function TreeHoverPreviewHost() {
  const snapshot = React.useSyncExternalStore(subscribe, () => state, () => state);
  const [mounted, setMounted] = React.useState(false);
  React.useEffect(() => {
    setMounted(true);
    const onScroll = () => hideTreePreview();
    window.addEventListener("scroll", onScroll, true);
    window.addEventListener("blur", onScroll);
    return () => {
      window.removeEventListener("scroll", onScroll, true);
      window.removeEventListener("blur", onScroll);
      hideTreePreview();
    };
  }, []);
  if (!mounted) return null;
  const { target, visible } = snapshot;

  return createPortal(
    <AnimatePresence>
      {visible && target && (
        <m.div
          key="tree-hover-preview"
          role="tooltip"
          variants={popoverFromLeft}
          initial="hidden"
          animate="shown"
          exit="hidden"
          layout="position"
          transition={{ layout: quick }}
          style={{ top: target.top, left: target.left }}
          className="pointer-events-none fixed z-overlay w-80 max-w-[calc(100vw-var(--space-4))] rounded-xl border border-border bg-surface-raised p-space-3 text-foreground shadow-ui-md dark:bg-surface-panel"
        >
          <div data-tree-row-preview>{target.preview}</div>
        </m.div>
      )}
    </AnimatePresence>,
    document.body
  );
}
