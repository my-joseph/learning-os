import type { ReactNode } from "react";
import { StudioLabHeader } from "@/components/shell/StudioHeader";

export default function LabLayout({ children }: { children: ReactNode }) {
  return (
    <>
      <StudioLabHeader />
      <main className="mx-auto w-full max-w-screen-xl px-space-4 py-space-6 sm:px-space-6 sm:py-space-8 lg:px-space-8">
        {children}
      </main>
    </>
  );
}
