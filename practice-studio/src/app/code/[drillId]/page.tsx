import { WorkspaceDrillRoute } from "@/components/shell/WorkspaceDrillRoute";

interface CodeDrillPageProps {
  params: { drillId: string };
  searchParams: { q?: string | string[] };
}

export default function CodeDrillPage({ params, searchParams }: CodeDrillPageProps) {
  return (
    <WorkspaceDrillRoute
      workspace="code"
      drillId={params.drillId}
      searchParams={searchParams}
    />
  );
}
