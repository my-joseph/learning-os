import type { InferSchema, Schema } from "./result.ts";

export function arraySchema<T>(_itemSchema: Schema<T>): Schema<T[]> {
  throw new Error("TODO [M3]: validate array elements with indexed paths");
}

export function optionalSchema<T>(_innerSchema: Schema<T>): Schema<T | undefined> {
  throw new Error("TODO [M3]: allow undefined or parse inner schema");
}

export function unionSchema<const Schemas extends readonly Schema<unknown>[]>(
  ..._schemas: Schemas
): Schema<InferSchema<Schemas[number]>> {
  throw new Error("TODO [M3]: try branches in order and report all branch issues on failure");
}
