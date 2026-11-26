import { PlaygroundBackLink } from "@/components/playground/PlaygroundBackLink";
import { Heading } from "@/components/ui/Heading";

export default function LabNotFound() {
  return (
    <div className="space-y-space-4">
      <PlaygroundBackLink />
      <Heading>Experiment not found</Heading>
    </div>
  );
}
