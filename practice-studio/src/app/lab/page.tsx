import type { Metadata } from "next";
import { LabCard } from "@/components/lab/LabCard";
import { LabPreview } from "@/components/lab/LabPreview";
import { labExperiments } from "@/components/lab/experiments";
import { Heading } from "@/components/ui/Heading";

export const metadata: Metadata = { title: "Lab · Practice Studio" };

export default function LabPage() {
  return (
    <div className="space-y-space-6">
      <div className="space-y-space-2">
        <Heading>Lab</Heading>
        <p className="text-sm text-foreground-secondary">Visual experiments — not used in drills yet.</p>
      </div>
      <ul className="grid grid-cols-1 gap-space-4 md:grid-cols-2 lg:grid-cols-4">
        {labExperiments.map((experiment) => (
          <li key={experiment.id} className="min-w-0">
            <LabCard experiment={experiment}>
              <LabPreview id={experiment.id} />
            </LabCard>
          </li>
        ))}
      </ul>
    </div>
  );
}
