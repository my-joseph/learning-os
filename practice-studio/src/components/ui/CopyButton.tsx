import React, { useState, type ReactNode } from "react";
import { Button } from "@/components/ui/shadcn/Button";

interface CopyButtonProps {
  text: string;
  className: string;
  children: ReactNode;
  copiedContent: ReactNode;
  timeoutMs?: number;
  title?: string;
  ariaLabel?: string;
  requireClipboard?: boolean;
}

export function CopyButton({
  text,
  className,
  children,
  copiedContent,
  timeoutMs = 1200,
  title,
  ariaLabel,
  requireClipboard = false,
}: CopyButtonProps) {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    if (typeof navigator === "undefined" || !navigator.clipboard) {
      if (requireClipboard) return;
    } else {
      void navigator.clipboard.writeText(text);
    }
    setCopied(true);
    window.setTimeout(() => setCopied(false), timeoutMs);
  };

  return (
    <Button
      variant="ghost"
      size="compact"
      onClick={handleCopy}
      title={title}
      aria-label={ariaLabel}
      className={className}
    >
      {copied ? copiedContent : children}
    </Button>
  );
}
