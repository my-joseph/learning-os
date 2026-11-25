"use client";

/*
 * Adapted from https://ui.shadcn.com/r/styles/radix-nova/code-block.json.
 *
 * MIT License
 *
 * Copyright (c) 2023 shadcn
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 */
import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/cn";

const codeBlockVariants = cva(
  "relative flex w-full min-w-0 flex-col overflow-hidden rounded-xl border border-border bg-surface-panel text-foreground",
  {
    variants: {
      variant: {
        full: "mb-space-4 text-xs md:text-sm",
        compact: "text-xs",
      },
    },
    defaultVariants: { variant: "compact" },
  }
);

export function CodeBlock({
  className,
  variant,
  ...props
}: React.ComponentProps<"div"> & VariantProps<typeof codeBlockVariants>) {
  return (
    <div
      data-slot="code-block"
      className={cn(codeBlockVariants({ variant }), className)}
      {...props}
    />
  );
}

export function CodeBlockHeader({ className, ...props }: React.ComponentProps<"div">) {
  return (
    <div
      data-slot="code-block-header"
      className={cn(
        "flex min-w-0 items-center gap-space-2 border-b border-border bg-surface-raised px-space-3_5 py-space-1",
        className
      )}
      {...props}
    />
  );
}

export function CodeBlockTitle({ className, ...props }: React.ComponentProps<"div">) {
  return (
    <div
      data-slot="code-block-title"
      className={cn("min-w-0 truncate font-mono text-xs font-medium", className)}
      {...props}
    />
  );
}

export function CodeBlockActions({ className, ...props }: React.ComponentProps<"div">) {
  return (
    <div
      data-slot="code-block-actions"
      className={cn("ms-auto flex shrink-0 items-center gap-space-1", className)}
      {...props}
    />
  );
}

export function CodeBlockContent({
  className,
  children,
  wrap = false,
  lineNumbers = false,
  ...props
}: React.ComponentProps<"pre"> & { wrap?: boolean; lineNumbers?: boolean }) {
  return (
    <pre
      data-slot="code-block-content"
      data-wrap={wrap || undefined}
      data-numbered={lineNumbers || undefined}
      dir="ltr"
      tabIndex={0}
      className={cn(
        "min-h-0 min-w-0 overflow-auto px-space-3_5 py-space-2_5 text-start font-mono leading-relaxed",
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-accent",
        wrap ? "whitespace-pre-wrap break-words" : "whitespace-pre",
        className
      )}
      {...props}
    >
      <code
        data-slot="code-block-code"
        className={lineNumbers ? "grid min-w-max grid-cols-[auto_1fr]" : undefined}
      >
        {children}
      </code>
    </pre>
  );
}

const codeBlockLineVariants = cva(
  "col-span-2 grid grid-cols-subgrid gap-x-space-3 rounded-sm px-space-1",
  {
    variants: {
      variant: {
        default: "",
        highlighted: "bg-surface-selected",
      },
    },
    defaultVariants: { variant: "default" },
  }
);

export function CodeBlockLine({
  className,
  variant,
  children,
  number,
  ...props
}: React.ComponentProps<"span"> &
  VariantProps<typeof codeBlockLineVariants> & { number: number }) {
  return (
    <span
      data-slot="code-block-line"
      data-variant={variant ?? "default"}
      className={cn(codeBlockLineVariants({ variant }), className)}
      {...props}
    >
      <span aria-hidden="true" className="select-none text-end text-xs tabular-nums text-muted">
        {number}
      </span>
      <span data-slot="code-block-line-content">{children || "\n"}</span>
    </span>
  );
}
