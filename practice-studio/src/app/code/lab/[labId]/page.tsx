import { WorkspaceDrillRoute } from "@/components/shell/WorkspaceDrillRoute";

interface CodeLabPageProps {
  params: { labId: string };
  searchParams: { m?: string | string[]; q?: string | string[] };
}

export default function CodeLabPage({ params, searchParams }: CodeLabPageProps) {
  return (
    <WorkspaceDrillRoute
      workspace="code"
      drillId={params.labId}
      searchParams={searchParams}
      isLabRoute={true}
    />
  );
}
