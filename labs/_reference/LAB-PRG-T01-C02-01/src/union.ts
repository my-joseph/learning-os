import { err, ok } from "./result.ts";
import type { InferSchema, Schema, ValidationIssue } from "./result.ts";

function formatIndexPath(pathPrefix: string | undefined, index: number): string {
  if (pathPrefix === undefined || pathPrefix.length === 0) {
    return `[${index}]`;
  }
  return `${pathPrefix}[${index}]`;
}

export function arraySchema<T>(itemSchema: Schema<T>): Schema<T[]> {
  return {
    parse(input: unknown, pathPrefix?: string) {
      if (!Array.isArray(input)) {
        const root = pathPrefix === undefined || pathPrefix.length === 0 ? "<root>" : pathPrefix;
        return err({ issues: [{ path: root, message: "Expected an array" }] });
      }
      const values: T[] = [];
      const issues: ValidationIssue[] = [];
      for (let i = 0; i < input.length; i += 1) {
        const parsed = itemSchema.parse(input[i], formatIndexPath(pathPrefix, i));
        if (parsed.ok) {
          values.push(parsed.value);
        } else {
          issues.push(...parsed.error.issues);
        }
      }
      return issues.length > 0 ? err({ issues }) : ok(values);
    },
  };
}

export function optionalSchema<T>(innerSchema: Schema<T>): Schema<T | undefined> {
  return {
    parse(input: unknown, pathPrefix?: string) {
      if (input === undefined) {
        return ok(undefined);
      }
      return innerSchema.parse(input, pathPrefix);
    },
  };
}

export function unionSchema<const Schemas extends readonly Schema<unknown>[]>(
  ...schemas: Schemas
): Schema<InferSchema<Schemas[number]>> {
  return {
    parse(input: unknown, pathPrefix?: string) {
      const branchIssues: ValidationIssue[] = [];
      for (const candidate of schemas) {
        const parsed = candidate.parse(input, pathPrefix);
        if (parsed.ok) {
          return ok(parsed.value as InferSchema<Schemas[number]>);
        }
        branchIssues.push(...parsed.error.issues);
      }
      return err({ issues: branchIssues });
    },
  };
}
