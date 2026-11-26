import { LabBackLink } from "@/components/lab/LabBackLink";
import { Heading } from "@/components/ui/Heading";

export default function LabNotFound() {
  return (
    <div className="space-y-space-4">
      <LabBackLink />
      <Heading>Experiment not found</Heading>
    </div>
  );
}
