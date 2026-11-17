import { err, ok } from "./result.ts";
import type { InferSchema, Schema, ValidationIssue } from "./result.ts";

function formatPath(pathPrefix: string | undefined, segment?: string): string {
  if (pathPrefix === undefined || pathPrefix.length === 0) {
    return segment ?? "<root>";
  }
  if (segment === undefined || segment.length === 0) {
    return pathPrefix;
  }
  return `${pathPrefix}.${segment}`;
}

function isPlainRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

export function stringSchema(): Schema<string> {
  return {
    parse(input: unknown, pathPrefix?: string) {
      if (typeof input !== "string") {
        return err({ issues: [{ path: formatPath(pathPrefix), message: "Expected a string" }] });
      }
      return ok(input);
    },
  };
}

export function numberSchema(): Schema<number> {
  return {
    parse(input: unknown, pathPrefix?: string) {
      if (typeof input !== "number" || !Number.isFinite(input)) {
        return err({ issues: [{ path: formatPath(pathPrefix), message: "Expected a finite number" }] });
      }
      return ok(input);
    },
  };
}

export function booleanSchema(): Schema<boolean> {
  return {
    parse(input: unknown, pathPrefix?: string) {
      if (typeof input !== "boolean") {
        return err({ issues: [{ path: formatPath(pathPrefix), message: "Expected a boolean" }] });
      }
      return ok(input);
    },
  };
}

export function literalSchema<const T extends string | number | boolean>(expected: T): Schema<T> {
  return {
    parse(input: unknown, pathPrefix?: string) {
      if (input !== expected) {
        return err({
          issues: [{ path: formatPath(pathPrefix), message: `Expected literal ${String(expected)}` }],
        });
      }
      return ok(expected);
    },
  };
}

function parseShapeEntries(
  input: Record<string, unknown>,
  shape: Record<string, Schema<unknown>>,
  pathPrefix: string | undefined,
): { readonly entries: Array<[string, unknown]>; readonly issues: ValidationIssue[] } {
  const entries: Array<[string, unknown]> = [];
  const issues: ValidationIssue[] = [];
  for (const [key, fieldSchema] of Object.entries(shape)) {
    const fieldPath = formatPath(pathPrefix, key);
    const hasOwn = Object.prototype.hasOwnProperty.call(input, key);
    const rawValue = hasOwn ? Object.getOwnPropertyDescriptor(input, key)?.value : undefined;
    const parsed = fieldSchema.parse(rawValue, fieldPath);
    if (parsed.ok) {
      entries.push([key, parsed.value]);
    } else {
      issues.push(...parsed.error.issues);
    }
  }
  return { entries, issues };
}

export function objectSchema<Shape extends Record<string, Schema<unknown>>>(
  shape: Shape,
): Schema<{ [K in keyof Shape]: InferSchema<Shape[K]> }> {
  return {
    parse(input: unknown, pathPrefix?: string) {
      if (!isPlainRecord(input)) {
        return err({ issues: [{ path: formatPath(pathPrefix), message: "Expected an object" }] });
      }
      const { entries, issues } = parseShapeEntries(input, shape, pathPrefix);
      if (issues.length > 0) {
        return err({ issues });
      }
      const built = Object.fromEntries(entries) as { [K in keyof Shape]: InferSchema<Shape[K]> };
      return ok(built);
    },
  };
}
