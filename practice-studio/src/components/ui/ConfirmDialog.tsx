"use client";

import React, { useId, useRef } from "react";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/shadcn/AlertDialog";

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

/** Reusable accessible confirmation dialog with Cancel focused by default. */
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
  const previousFocusRef = useRef<HTMLElement | null>(null);

  return (
    <AlertDialog
      open={open}
      onOpenChange={(nextOpen) => {
        if (!nextOpen) {
          onCancel();
        }
      }}
    >
      <AlertDialogContent
        aria-modal="true"
        aria-labelledby={titleId}
        aria-describedby={descriptionId}
        onOpenAutoFocus={(e) => {
          previousFocusRef.current =
            document.activeElement instanceof HTMLElement ? document.activeElement : null;
          e.preventDefault();
          cancelRef.current?.focus();
        }}
        onCloseAutoFocus={(e) => {
          e.preventDefault();
          const prev = previousFocusRef.current;
          previousFocusRef.current = null;
          if (prev && prev.isConnected) {
            prev.focus();
          }
        }}
        className="max-w-sm gap-4 p-5 shadow-lg"
      >
        <AlertDialogHeader className="gap-1.5">
          <AlertDialogTitle
            id={titleId}
            className="text-base font-semibold text-zinc-900 dark:text-zinc-100"
          >
            {title}
          </AlertDialogTitle>
          <AlertDialogDescription id={descriptionId}>
            {description}
          </AlertDialogDescription>
        </AlertDialogHeader>

        <AlertDialogFooter className="flex-row justify-end gap-2">
          <AlertDialogCancel
            ref={cancelRef}
            className="rounded-xl text-xs font-normal"
          >
            {cancelLabel}
          </AlertDialogCancel>
          <AlertDialogAction
            variant={destructive ? "destructive" : "primary"}
            onClick={(e) => {
              e.preventDefault();
              onConfirm();
            }}
            className="rounded-xl text-xs font-semibold"
          >
            {confirmLabel}
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
};
