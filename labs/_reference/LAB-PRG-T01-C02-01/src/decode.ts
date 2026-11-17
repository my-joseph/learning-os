import { err, ok } from "./result.ts";
import type { Result, Schema, ValidationIssue } from "./result.ts";

export type ApiDecodeError =
  | { readonly kind: "invalid-json"; readonly message: string }
  | { readonly kind: "validation-failed"; readonly issues: readonly ValidationIssue[] };

export function decodeApiPayload<T>(rawJson: string, schema: Schema<T>): Result<T, ApiDecodeError> {
  let parsedJson: unknown;
  try {
    parsedJson = JSON.parse(rawJson);
  } catch (caught: unknown) {
    const message = caught instanceof Error ? caught.message : "Invalid JSON input";
    return err({ kind: "invalid-json", message });
  }
  const validated = schema.parse(parsedJson);
  if (!validated.ok) {
    return err({ kind: "validation-failed", issues: validated.error.issues });
  }
  return ok(validated.value);
}

export function formatDecodeError(error: ApiDecodeError): string {
  switch (error.kind) {
    case "invalid-json":
      return `Invalid JSON: ${error.message}`;
    case "validation-failed":
      return error.issues.map((issue) => `${issue.path}: ${issue.message}`).join("; ");
    default: {
      const unreachable: never = error;
      return unreachable;
    }
  }
}
