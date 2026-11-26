import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { LabBackLink } from "@/components/lab/LabBackLink";
import { LabShowcase } from "@/components/lab/LabShowcase";
import { ShapeGallery } from "@/components/lab/ShapeGallery";
import { labExperiments } from "@/components/lab/experiments";
import { DiskMethodShowcase } from "@/components/ui-poc/DiskMethodShowcase";
import { CubeShowcase, LeverShowcase, PulleyShowcase } from "@/components/ui-poc/IsometricShowcase";
import { ShadcnPocShowcase } from "@/components/ui-poc/ShadcnPocShowcase";
import { Heading } from "@/components/ui/Heading";

type Props = { params: { id: string } };

export function generateStaticParams() {
  return labExperiments.map(({ id }) => ({ id }));
}

export function generateMetadata({ params }: Props): Metadata {
  const experiment = labExperiments.find(({ id }) => id === params.id);
  return { title: experiment ? `${experiment.title} · Lab · Practice Studio` : "Lab · Practice Studio" };
}

function ShapesShowcase() {
  return <LabShowcase title="Signature shapes" caption="12 contours" figure={<ShapeGallery />} />;
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
  const experiment = labExperiments.find(({ id }) => id === params.id);
  if (!experiment) notFound();
  const Showcase = showcases[experiment.id];
  return (
    <div className="space-y-space-4">
      <LabBackLink />
      <Heading>{experiment.title}</Heading>
      <Showcase />
    </div>
  );
}
