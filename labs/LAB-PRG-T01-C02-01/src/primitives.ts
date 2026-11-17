import type { InferSchema, Schema } from "./result.ts";

export function stringSchema(): Schema<string> {
  throw new Error("TODO [M2]: validate string values");
}

export function numberSchema(): Schema<number> {
  throw new Error("TODO [M2]: validate finite number values");
}

export function booleanSchema(): Schema<boolean> {
  throw new Error("TODO [M2]: validate boolean values");
}

export function literalSchema<const T extends string | number | boolean>(_expected: T): Schema<T> {
  throw new Error("TODO [M2]: validate exact literal value");
}

export function objectSchema<Shape extends Record<string, Schema<unknown>>>(
  _shape: Shape,
): Schema<{ [K in keyof Shape]: InferSchema<Shape[K]> }> {
  throw new Error("TODO [M2]: validate plain object properties against shape");
}
