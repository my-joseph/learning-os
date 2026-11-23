"use client";

import React, { useCallback, useEffect, useRef, useState } from "react";
import { AnimatePresence, m } from "motion/react";
import { AlertCircle, AlertTriangle, CheckCircle2, Loader2, X } from "lucide-react";
import { StatusMessage } from "@/hooks/types";
import { toastVariants } from "@/lib/motion";
import { statusTone, warningTone } from "@/lib/statusTone";
import {
  ToastItem,
  dismissToast,
  enqueueToast,
  getToastDurationMs,
  isInProgressToast,
} from "@/lib/toast";

interface ToastItemRowProps {
  item: ToastItem;
  onDismiss: (id: string) => void;
}

const ToastItemRow: React.FC<ToastItemRowProps> = ({ item, onDismiss }) => {
  const { message } = item;
  const isFail = message.type === "fail";
  const inProgress = isInProgressToast(message);
  const initialDuration = getToastDurationMs(message);

  const [paused, setPaused] = useState(false);
  const remainingRef = useRef<number | null>(initialDuration);
  const startedAtRef = useRef<number>(0);

  useEffect(() => {
    if (remainingRef.current === null || paused) return;
    const delay = remainingRef.current;
    if (delay <= 0) {
      onDismiss(item.id);
      return;
    }

    startedAtRef.current = Date.now();
    const timer = setTimeout(() => {
      remainingRef.current = 0;
      onDismiss(item.id);
    }, delay);

    return () => {
      clearTimeout(timer);
      if (startedAtRef.current > 0) {
        const elapsed = Date.now() - startedAtRef.current;
        remainingRef.current = Math.max(0, delay - elapsed);
      }
    };
  }, [item.id, paused, onDismiss]);

  return (
    <m.div
      variants={toastVariants}
      initial="hidden"
      animate="shown"
      exit="exit"
      role={isFail ? "alert" : "status"}
      aria-live={isFail ? undefined : "polite"}
      onMouseEnter={() => setPaused(true)}
      onMouseLeave={() => setPaused(false)}
      onFocus={() => setPaused(true)}
      onBlur={() => setPaused(false)}
      className="pointer-events-auto bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-xl shadow-md px-3.5 py-2.5 flex items-start gap-2.5 text-sm text-zinc-800 dark:text-zinc-200"
    >
      {message.type === "pass" ? (
        <CheckCircle2
          className={`w-4 h-4 ${statusTone.correct.text} shrink-0 mt-0.5`}
          aria-hidden="true"
        />
      ) : isFail ? (
        <AlertCircle
          className={`w-4 h-4 ${statusTone.wrong.text} shrink-0 mt-0.5`}
          aria-hidden="true"
        />
      ) : inProgress ? (
        <Loader2
          className={`w-4 h-4 ${warningTone.text} shrink-0 mt-0.5 animate-spin motion-reduce:animate-none`}
          aria-hidden="true"
        />
      ) : (
        <AlertTriangle
          className={`w-4 h-4 ${warningTone.text} shrink-0 mt-0.5`}
          aria-hidden="true"
        />
      )}

      <span className="flex-1 min-w-0 leading-snug break-words">
        {message.text}
      </span>

      <button
        type="button"
        onClick={() => onDismiss(item.id)}
        aria-label="Dismiss notification"
        className="inline-flex items-center justify-center min-h-[44px] min-w-[44px] sm:min-h-0 sm:min-w-0 sm:w-6 sm:h-6 -mr-2.5 -my-2 sm:-mr-1 sm:-mt-0.5 sm:my-0 rounded-lg text-zinc-500 hover:text-zinc-900 dark:text-zinc-400 dark:hover:text-zinc-100 hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-colors motion-reduce:transition-none focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-600 dark:focus-visible:ring-indigo-400 shrink-0"
      >
        <X className="w-3.5 h-3.5" aria-hidden="true" />
      </button>
    </m.div>
  );
};

interface ToastStackProps {
  status: StatusMessage | null;
  onClearStatus: () => void;
}

/** Stacked status toasts anchored bottom-right (>=640px) or bottom-centre (<640px). */
export const ToastStack: React.FC<ToastStackProps> = ({
  status,
  onClearStatus,
}) => {
  const [toasts, setToasts] = useState<ToastItem[]>([]);
  const nextIdRef = useRef(1);
  const prevStatusRef = useRef<StatusMessage | null>(null);
  const hadToastsRef = useRef(false);

  useEffect(() => {
    if (status === prevStatusRef.current) return;
    prevStatusRef.current = status;

    if (!status) {
      setToasts([]);
      return;
    }

    const id = `toast-${nextIdRef.current++}`;
    setToasts((prev) => enqueueToast(prev, status, id));
  }, [status]);

  const handleDismiss = useCallback((id: string) => {
    setToasts((prev) => dismissToast(prev, id));
  }, []);

  useEffect(() => {
    if (toasts.length > 0) {
      hadToastsRef.current = true;
    } else if (hadToastsRef.current) {
      hadToastsRef.current = false;
      if (prevStatusRef.current !== null) {
        prevStatusRef.current = null;
        onClearStatus();
      }
    }
  }, [toasts.length, onClearStatus]);

  return (
    <div className="fixed bottom-4 left-2 right-2 sm:left-auto sm:right-4 sm:w-full sm:max-w-sm z-50 flex flex-col gap-2 pointer-events-none">
      <AnimatePresence initial={false}>
        {toasts.map((item) => (
          <ToastItemRow key={item.id} item={item} onDismiss={handleDismiss} />
        ))}
      </AnimatePresence>
    </div>
  );
};
