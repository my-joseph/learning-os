"use client";

import React from "react";
import dynamic from "next/dynamic";
import { Skeleton } from "@/components/ui/shadcn/Skeleton";
import "./isometric.css";

function DiskMethodSkeleton() {
  return (
    <div className="iso-figure-box w-full p-space-4" aria-hidden="true">
      <Skeleton className="h-full w-full rounded-xl" />
    </div>
  );
}

export const LazyDiskMethod = dynamic(
  () => import("@/components/isometric/disk-method").then((mod) => mod.DiskMethod),
  {
    ssr: false,
    loading: () => <DiskMethodSkeleton />,
  },
);
