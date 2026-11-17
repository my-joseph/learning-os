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

export function ok<T>(value: T): Result<T, never> {
  return { ok: true, value };
}

export function err<E>(error: E): Result<never, E> {
  return { ok: false, error };
}

export function mapResult<T, U, E>(result: Result<T, E>, fn: (value: T) => U): Result<U, E> {
  if (!result.ok) {
    return result;
  }
  return ok(fn(result.value));
}

export function flatMapResult<T, U, E>(
  result: Result<T, E>,
  fn: (value: T) => Result<U, E>,
): Result<U, E> {
  if (!result.ok) {
    return result;
  }
  return fn(result.value);
}
