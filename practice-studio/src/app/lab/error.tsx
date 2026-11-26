"use client";

import { LabBackLink } from "@/components/lab/LabBackLink";
import { Heading } from "@/components/ui/Heading";
import { Button } from "@/components/ui/shadcn/Button";

export default function LabError({ reset }: { reset: () => void }) {
  return (
    <div className="space-y-space-4">
      <LabBackLink />
      <Heading>The experiment could not load</Heading>
      <Button variant="outline" onClick={reset}>Try again</Button>
    </div>
  );
}
