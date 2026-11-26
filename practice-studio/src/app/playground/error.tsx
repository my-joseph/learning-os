"use client";

import { PlaygroundBackLink } from "@/components/playground/PlaygroundBackLink";
import { Heading } from "@/components/ui/Heading";
import { Button } from "@/components/ui/shadcn/Button";

export default function LabError({ reset }: { reset: () => void }) {
  return (
    <div className="space-y-space-4">
      <PlaygroundBackLink />
      <Heading>The experiment could not load</Heading>
      <Button variant="outline" onClick={reset}>Try again</Button>
    </div>
  );
}
