import Link from "next/link";
import { ArrowLeft } from "lucide-react";
import { Button } from "@/components/ui/shadcn/Button";

export function PlaygroundBackLink() {
  return (
    <Button asChild variant="exampleBack" size="exampleBack" className="text-sm">
      <Link href="/playground">
        <ArrowLeft className="size-space-4" aria-hidden="true" />
        Playground
      </Link>
    </Button>
  );
}
