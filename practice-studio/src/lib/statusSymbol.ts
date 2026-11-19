import { statusTone } from "./statusTone";

export type StatusSymbolKind =
  | "pass"
  | "fail"
  | "revise"
  | "not_run"
  | "none"
  | "not_requested";

export function statusSymbolClass(kind: StatusSymbolKind): string {
  if (kind === "pass") return `${statusTone.correct.text} font-semibold`;
  if (kind === "fail" || kind === "revise") {
    return `${statusTone.wrong.text} font-semibold`;
  }
  return statusTone.notTried.text;
}
