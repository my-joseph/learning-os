import { WorkspaceDrillRoute } from "@/components/shell/WorkspaceDrillRoute";

interface MathDrillPageProps {
  params: { drillId: string };
  searchParams: { q?: string | string[] };
}

export default function MathDrillPage({ params, searchParams }: MathDrillPageProps) {
  return (
    <WorkspaceDrillRoute
      workspace="math"
      drillId={params.drillId}
      searchParams={searchParams}
    />
  );
}
