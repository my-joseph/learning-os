/**
 * Pure physics calculations for 1D collisions between two carts on a level,
 * frictionless track (OpenStax College Physics 2e §8.1–8.5, University Physics
 * Vol. 1 §9.1–9.4, HyperPhysics Elastic/Inelastic Collisions).
 *
 * Sign convention: right (+x) is positive; left (-x) is negative.
 */

export const MIN_MASS_KG = 0.5;
export const MAX_MASS_KG = 5.0;
export const MASS_STEP_KG = 0.5;

export const MIN_VELOCITY_MPS = -3.0;
export const MAX_VELOCITY_MPS = 3.0;
export const VELOCITY_STEP_MPS = 0.5;

export const MIN_RESTITUTION = 0;
export const MAX_RESTITUTION = 1;
export const RESTITUTION_STEP = 0.05;

export const TRACK_HALF_SPAN_M = 3.0;
export const INITIAL_CART1_POS_M = -1.2;
export const INITIAL_CART2_POS_M = 1.2;

export type CollisionKind = "elastic" | "inelastic" | "perfectly-inelastic" | "no-collision";

export type CollisionInput = {
  /** Mass of cart 1 (left cart) in kg (> 0). */
  m1: number;
  /** Mass of cart 2 (right cart) in kg (> 0). */
  m2: number;
  /** Initial signed velocity of cart 1 in m/s (right = +). */
  v1: number;
  /** Initial signed velocity of cart 2 in m/s (right = +). */
  v2: number;
  /** Coefficient of restitution e in [0, 1] (1 = elastic, 0 = stick together). */
  e: number;
};

export type CollisionTheory = {
  m1: number;
  m2: number;
  v1: number;
  v2: number;
  e: number;
  /** True when cart 1 (on the left) approaches cart 2 (on the right): v1 > v2. */
  willCollide: boolean;
  collisionKind: CollisionKind;
  /** Theoretical post-collision velocity of cart 1 in m/s. */
  v1After: number;
  /** Theoretical post-collision velocity of cart 2 in m/s. */
  v2After: number;
  p1Before: number;
  p2Before: number;
  pBefore: number;
  p1After: number;
  p2After: number;
  pAfter: number;
  ke1Before: number;
  ke2Before: number;
  keBefore: number;
  ke1After: number;
  ke2After: number;
  keAfter: number;
  /** Kinetic energy dissipated (J): keBefore - keAfter (>= 0). */
  keLost: number;
};

export type InstantaneousMetrics = {
  p1: number;
  p2: number;
  totalP: number;
  ke1: number;
  ke2: number;
  totalKe: number;
};

export const DEFAULT_COLLISION_INPUT: CollisionInput = {
  m1: 2.0,
  m2: 2.0,
  v1: 2.0,
  v2: 0.0,
  e: 1.0,
};

function assertFinite(value: number, name: string): number {
  if (!Number.isFinite(value)) {
    throw new RangeError(`${name} must be a finite number`);
  }
  return value;
}

function assertPositive(value: number, name: string): number {
  assertFinite(value, name);
  if (value <= 0) {
    throw new RangeError(`${name} must be greater than 0`);
  }
  return value;
}

function assertRestitution(value: number): number {
  assertFinite(value, "e");
  if (value < 0 || value > 1) {
    throw new RangeError("e must be between 0 and 1");
  }
  return value;
}

function zeroNegativeZero(n: number): number {
  return Math.abs(n) < 1e-12 ? 0 : n;
}

/**
 * Computes momentum (kg·m/s) and kinetic energy (J) for a two-cart state.
 */
export function computeInstantaneousMetrics(
  m1: number,
  m2: number,
  v1: number,
  v2: number,
): InstantaneousMetrics {
  assertPositive(m1, "m1");
  assertPositive(m2, "m2");
  assertFinite(v1, "v1");
  assertFinite(v2, "v2");

  const p1 = zeroNegativeZero(m1 * v1);
  const p2 = zeroNegativeZero(m2 * v2);
  const totalP = zeroNegativeZero(p1 + p2);
  const ke1 = 0.5 * m1 * v1 * v1;
  const ke2 = 0.5 * m2 * v2 * v2;
  const totalKe = ke1 + ke2;

  return { p1, p2, totalP, ke1, ke2, totalKe };
}

/**
 * Computes the analytical 1D collision result for two carts (cart 1 initially
 * to the left of cart 2 on a frictionless horizontal track).
 */
export function computeCollisionTheory(input: CollisionInput): CollisionTheory {
  const m1 = assertPositive(input.m1, "m1");
  const m2 = assertPositive(input.m2, "m2");
  const v1 = assertFinite(input.v1, "v1");
  const v2 = assertFinite(input.v2, "v2");
  const e = assertRestitution(input.e);

  const before = computeInstantaneousMetrics(m1, m2, v1, v2);
  const willCollide = v1 - v2 > 1e-9;

  const totalMass = m1 + m2;
  const v1After = willCollide
    ? zeroNegativeZero((m1 * v1 + m2 * v2 + m2 * e * (v2 - v1)) / totalMass)
    : zeroNegativeZero(v1);
  const v2After = willCollide
    ? zeroNegativeZero((m1 * v1 + m2 * v2 + m1 * e * (v1 - v2)) / totalMass)
    : zeroNegativeZero(v2);

  const after = computeInstantaneousMetrics(m1, m2, v1After, v2After);
  const keLost = willCollide ? zeroNegativeZero(Math.max(0, before.totalKe - after.totalKe)) : 0;

  let collisionKind: CollisionKind;
  if (!willCollide) {
    collisionKind = "no-collision";
  } else if (Math.abs(e - 1) < 1e-9) {
    collisionKind = "elastic";
  } else if (e < 1e-9) {
    collisionKind = "perfectly-inelastic";
  } else {
    collisionKind = "inelastic";
  }

  return {
    m1,
    m2,
    v1: zeroNegativeZero(v1),
    v2: zeroNegativeZero(v2),
    e,
    willCollide,
    collisionKind,
    v1After,
    v2After,
    p1Before: before.p1,
    p2Before: before.p2,
    pBefore: before.totalP,
    p1After: after.p1,
    p2After: after.p2,
    pAfter: after.totalP,
    ke1Before: before.ke1,
    ke2Before: before.ke2,
    keBefore: before.totalKe,
    ke1After: after.ke1,
    ke2After: after.ke2,
    keAfter: after.totalKe,
    keLost,
  };
}

/**
 * Cart width in meters as a subtle visual indicator of mass (0.62 m to 0.90 m).
 */
export function cartWidthMeters(massKg: number): number {
  const t = Math.max(0, Math.min(1, (massKg - MIN_MASS_KG) / (MAX_MASS_KG - MIN_MASS_KG)));
  return 0.62 + t * 0.28;
}

/**
 * Cart height in meters as a subtle visual indicator of mass (0.56 m to 0.78 m).
 */
export function cartHeightMeters(massKg: number): number {
  const t = Math.max(0, Math.min(1, (massKg - MIN_MASS_KG) / (MAX_MASS_KG - MIN_MASS_KG)));
  return 0.56 + t * 0.22;
}

/**
 * Computes percentage error between a measured velocity and analytical theory.
 * Returns 0 when both are near zero; uses |theory| as denominator when |theory| >= 0.05 m/s,
 * or max(0.05, |theory|) otherwise to avoid division by zero on stopped carts.
 */
export function velocityErrorPercent(measured: number, theory: number): number {
  const diff = Math.abs(measured - theory);
  if (diff < 1e-6) return 0;
  const denom = Math.max(0.05, Math.abs(theory));
  return (diff / denom) * 100;
}
