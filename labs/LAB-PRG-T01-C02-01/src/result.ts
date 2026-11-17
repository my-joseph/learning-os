export type Result<T, E> =
  | { readonly ok: true; readonly value: T }
  | { readonly ok: false; readonly error: E };

export interface ValidationIssue {
  readonly path: string;
  readonly message: string;
}

export interface SchemaError {
  readonly issues: readonly ValidationIssue[];
}

export interface Schema<T> {
  parse(input: unknown, pathPrefix?: string): Result<T, SchemaError>;
}

export type InferSchema<S> = S extends Schema<infer T> ? T : never;

export function ok<T>(_value: T): Result<T, never> {
  throw new Error("TODO [M1]: return ok Result variant");
}

export function err<E>(_error: E): Result<never, E> {
  throw new Error("TODO [M1]: return err Result variant");
}

export function mapResult<T, U, E>(_result: Result<T, E>, _fn: (value: T) => U): Result<U, E> {
  throw new Error("TODO [M1]: transform ok value while passing err through");
}

export function flatMapResult<T, U, E>(_result: Result<T, E>, _fn: (value: T) => Result<U, E>): Result<U, E> {
  throw new Error("TODO [M1]: chain Result-returning transformation");
}
