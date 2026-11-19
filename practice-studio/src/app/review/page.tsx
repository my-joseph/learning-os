import React, { Suspense } from "react";
import { DailyReviewPage } from "@/components/review/DailyReviewPage";

export const dynamic = "force-dynamic";

export default function ReviewRoutePage() {
  return (
    <Suspense fallback={null}>
      <DailyReviewPage />
    </Suspense>
  );
}
