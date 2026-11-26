import type { Metadata } from "next";
import { PlaygroundExperimentCard } from "@/components/playground/PlaygroundPreview";
import { playgroundExperiments } from "@/components/playground/experiments";
import { Heading } from "@/components/ui/Heading";

export const metadata: Metadata = { title: "Playground · Practice Studio" };

export default function LabPage() {
  return (
    <div className="space-y-space-6">
      <div className="space-y-space-2">
        <Heading>Playground</Heading>
        <p className="text-sm text-foreground-secondary">Visual experiments — not used in drills yet.</p>
      </div>
      <ul className="grid grid-cols-1 gap-space-4 md:grid-cols-2 lg:grid-cols-4">
        {playgroundExperiments.map((experiment) => (
          <li key={experiment.id} className="min-w-0">
            <PlaygroundExperimentCard experiment={experiment} />
          </li>
        ))}
      </ul>
    </div>
  );
}
