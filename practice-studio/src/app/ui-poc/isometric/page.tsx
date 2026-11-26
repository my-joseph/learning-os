import { permanentRedirect } from "next/navigation";

export const dynamic = "force-dynamic";

export default function LegacyShowcasePage() {
  permanentRedirect("/playground/lever");
}
