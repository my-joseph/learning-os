# LAB-PRG-T01-C02-01 — Result & MiniSchema

## Scenario

Build a small runtime schema parser and `Result<T, E>` module for decoding external API payloads under strict TypeScript (`strict: true`). Unknown wire JSON must be validated cleanly without type assertions, preserving nested field paths and falsy domain values (`0`, `""`, `false`).

## Milestones

### M1 — Schema Types & `Result<T, E>` Union

Define the discriminated `Result<T, E>` union (`ok`/`err` constructors and combinators `mapResult` / `flatMapResult`), `ValidationIssue`, `SchemaError`, and the `Schema<T>` contract.

Run this milestone's visible checks with `npm run test:m1` and all checks with `npm run check:m1`.

### M2 — Primitive & Object Parsers

Implement `stringSchema`, `numberSchema` (rejecting non-finite numbers), `booleanSchema`, `literalSchema`, and `objectSchema` (validating required own properties without trusting prototype keys, preserving `0`/`""`/`false`, and collecting nested field paths).

Run this milestone's visible checks with `npm run test:m2` and all checks with `npm run check:m2`.

### M3 — Union & Nested Error Paths

Implement `arraySchema`, `optionalSchema`, and `unionSchema`. Preserve index and nested field paths across arrays and objects, and report failure issues from every failing union branch.

Run this milestone's visible checks with `npm run test:m3` and all checks with `npm run check:m3`.

### M4 — Strict `unknown` Narrowing & Wire Decoding

Implement `decodeApiPayload(rawJson, schema)` returning `Result<T, ApiDecodeError>` and an exhaustive `formatDecodeError(error)` helper. Reject malformed JSON, non-matching payloads, and missing required fields without unsafe casts.

Run this milestone's visible checks with `npm run test:m4` and all checks with `npm run check:m4`.

## Commands

- `npm test` runs all visible milestone tests.
- `npm run check` runs tests, lint, and typecheck.
- `npm run test:m1` / `npm run check:m1` run one milestone; use `m2`, `m3`, or `m4` for the others.
- `npm run review -- m1` prints the review request for the milestone.
- Ask Claude Code: `ตรวจโค้ด LAB-PRG-T01-C02-01 M1` (replace `M1` with the milestone being reviewed).
