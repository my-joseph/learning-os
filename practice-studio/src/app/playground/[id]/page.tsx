import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { PlaygroundBackLink } from "@/components/playground/PlaygroundBackLink";
import { PlaygroundShowcase } from "@/components/playground/PlaygroundShowcase";
import { ShapeGallery } from "@/components/playground/ShapeGallery";
import { playgroundExperiments } from "@/components/playground/experiments";
import { DiskMethodShowcase } from "@/components/ui-poc/DiskMethodShowcase";
import { CubeShowcase, LeverShowcase, PulleyShowcase } from "@/components/ui-poc/IsometricShowcase";
import { ShadcnPocShowcase } from "@/components/ui-poc/ShadcnPocShowcase";
import { Heading } from "@/components/ui/Heading";

type Props = { params: { id: string } };

export function generateStaticParams() {
  return playgroundExperiments.map(({ id }) => ({ id }));
}

export function generateMetadata({ params }: Props): Metadata {
  const experiment = playgroundExperiments.find(({ id }) => id === params.id);
  return { title: experiment ? `${experiment.title} · Playground · Practice Studio` : "Playground · Practice Studio" };
}

function ShapesShowcase() {
  return <PlaygroundShowcase title="Signature shapes" caption="12 contours" figure={<ShapeGallery />} />;
}

const showcases = {
  lever: LeverShowcase,
  pulley: PulleyShowcase,
  "disk-method": DiskMethodShowcase,
  cube: CubeShowcase,
  shapes: ShapesShowcase,
  "ui-components": ShadcnPocShowcase,
};

export default function LabDetailPage({ params }: Props) {
  const experiment = playgroundExperiments.find(({ id }) => id === params.id);
  if (!experiment) notFound();
  const Showcase = showcases[experiment.id];
  return (
    <div className="space-y-space-4">
      <PlaygroundBackLink />
      <Heading>{experiment.title}</Heading>
      <Showcase />
    </div>
  );
}
