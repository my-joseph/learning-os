import type { Result, Schema, ValidationIssue } from "./result.ts";

export type ApiDecodeError =
  | { readonly kind: "invalid-json"; readonly message: string }
  | { readonly kind: "validation-failed"; readonly issues: readonly ValidationIssue[] };

export function decodeApiPayload<T>(_rawJson: string, _schema: Schema<T>): Result<T, ApiDecodeError> {
  throw new Error("TODO [M4]: parse JSON safely and validate against schema");
}

export function formatDecodeError(_error: ApiDecodeError): string {
  throw new Error("TODO [M4]: exhaustively format ApiDecodeError variants");
}
