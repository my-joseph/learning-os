"use client";

import React, { useEffect, useId, useRef } from "react";
import { AnimatePresence, m } from "motion/react";
import { dialogCard, fade, presence } from "@/lib/motion";

export interface ConfirmDialogProps {
  open: boolean;
  title: string;
  description: string;
  confirmLabel?: string;
  cancelLabel?: string;
  destructive?: boolean;
  onConfirm: () => void;
  onCancel: () => void;
}

/** Reusable accessible confirmation dialog with Cancel focused by default and Motion enter/exit. */
export const ConfirmDialog: React.FC<ConfirmDialogProps> = ({
  open,
  title,
  description,
  confirmLabel = "Confirm",
  cancelLabel = "Cancel",
  destructive = true,
  onConfirm,
  onCancel,
}) => {
  const titleId = useId();
  const descriptionId = useId();
  const cancelRef = useRef<HTMLButtonElement | null>(null);
  const cardRef = useRef<HTMLDivElement | null>(null);
  const previousFocusRef = useRef<HTMLElement | null>(null);
  const wasOpenRef = useRef(false);

  // Capture trigger focus on open, default focus to Cancel, and restore trigger focus on close.
  useEffect(() => {
    if (open && !wasOpenRef.current) {
      previousFocusRef.current =
        document.activeElement instanceof HTMLElement ? document.activeElement : null;
      wasOpenRef.current = true;
      if (cancelRef.current) {
        cancelRef.current.focus();
      } else {
        const rafId = requestAnimationFrame(() => cancelRef.current?.focus());
        return () => cancelAnimationFrame(rafId);
      }
      return;
    }

    if (!open && wasOpenRef.current) {
      wasOpenRef.current = false;
      const prev = previousFocusRef.current;
      previousFocusRef.current = null;
      if (prev && prev.isConnected) {
        prev.focus();
      }
    }
  }, [open]);

  // Escape cancels; Tab wraps within dialog controls while open.
  useEffect(() => {
    if (!open) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        e.preventDefault();
        e.stopPropagation();
        onCancel();
        return;
      }

      if (e.key === "Tab" && cardRef.current) {
        const focusable = Array.from(
          cardRef.current.querySelectorAll<HTMLElement>(
            'button:not([disabled]), [href], input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])'
          )
        );
        if (focusable.length === 0) return;
        const first = focusable[0];
        const last = focusable[focusable.length - 1];
        if (e.shiftKey && document.activeElement === first) {
          e.preventDefault();
          last.focus();
        } else if (!e.shiftKey && document.activeElement === last) {
          e.preventDefault();
          first.focus();
        }
      }
    };

    window.addEventListener("keydown", handleKeyDown, true);
    return () => window.removeEventListener("keydown", handleKeyDown, true);
  }, [open, onCancel]);

  const confirmBtnCls = destructive
    ? "bg-rose-600 hover:bg-rose-700 dark:bg-rose-600 dark:hover:bg-rose-700 focus-visible:ring-indigo-600 dark:focus-visible:ring-indigo-400"
    : "bg-indigo-600 hover:bg-indigo-700 dark:bg-indigo-600 dark:hover:bg-indigo-700 focus-visible:ring-indigo-600 dark:focus-visible:ring-indigo-400";

  return (
    <AnimatePresence>
      {open && (
        <m.div
          key="confirm-dialog"
          {...presence}
          className="fixed inset-0 z-50 flex items-center justify-center p-4"
        >
          <m.div
            variants={fade}
            aria-hidden="true"
            onClick={onCancel}
            className="fixed inset-0 bg-zinc-950/40 backdrop-blur-[1px]"
          />
          <m.div
            ref={cardRef}
            variants={dialogCard}
            role="alertdialog"
            aria-modal="true"
            aria-labelledby={titleId}
            aria-describedby={descriptionId}
            className="relative z-10 w-full max-w-sm bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-2xl shadow-lg p-5 space-y-4"
          >
            <div className="space-y-1.5">
              <h2
                id={titleId}
                className="text-base font-semibold text-zinc-900 dark:text-zinc-100"
              >
                {title}
              </h2>
              <p
                id={descriptionId}
                className="text-sm text-zinc-600 dark:text-zinc-400"
              >
                {description}
              </p>
            </div>

            <div className="flex items-center justify-end gap-2">
              <button
                ref={cancelRef}
                type="button"
                onClick={onCancel}
                className="h-9 px-3.5 rounded-xl text-xs font-medium text-zinc-700 dark:text-zinc-300 bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-indigo-600 dark:focus-visible:ring-indigo-400 focus-visible:ring-offset-1"
              >
                {cancelLabel}
              </button>
              <button
                type="button"
                onClick={onConfirm}
                className={`h-9 px-3.5 rounded-xl text-xs font-semibold text-white transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-offset-1 ${confirmBtnCls}`}
              >
                {confirmLabel}
              </button>
            </div>
          </m.div>
        </m.div>
      )}
    </AnimatePresence>
  );
};
