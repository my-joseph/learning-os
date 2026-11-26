/**
 * Pure physics calculations for a first-class lever (seesaw) in static equilibrium.
 *
 * Formulas follow OpenStax College Physics 2e (§4.3 Weight W = m g, §9.2 Torque
 * tau = r F sin(theta) with net tau = 0 for equilibrium, §9.5 Simple Machines
 * MA = d_effort / d_load) and HyperPhysics (F_e * L_e = F_r * L_r).
 */

export const DEFAULT_GRAVITY = 9.8; // m/s^2
export const DEFAULT_BALANCE_TOLERANCE = 0.05; // N·m
export const LEVER_TICK_STEP = 0.5; // m
export const LEVER_BEAM_HALF_SPAN = 2.0; // m (-2.0 m to +2.0 m usable span)
export const LEVER_MASS_PRESETS = [5, 10, 15, 20, 25, 30] as const;

export type EffortSide = "left" | "right";
export type TiltDirection = "left" | "right" | "level";

export type LeverInput = {
  /** Left load mass in kg (>= 0). */
  m1: number;
  /** Left load distance from the fulcrum in m (>= 0). */
  d1: number;
  /** Right load mass in kg (>= 0). */
  m2: number;
  /** Right load distance from the fulcrum in m (>= 0). */
  d2: number;
  /** Gravitational acceleration in m/s^2 (defaults to 9.8). */
  g?: number;
  /** Optional effort side to compute ideal mechanical advantage (d_effort / d_load). */
  effortSide?: EffortSide;
  /** Equilibrium tolerance in N·m (defaults to 0.05). */
  tolerance?: number;
};

export type LeverState = {
  /** Left gravitational force (weight) in N. */
  w1: number;
  /** Right gravitational force (weight) in N. */
  w2: number;
  /** Magnitude of left (counterclockwise) torque in N·m. */
  tau1: number;
  /** Magnitude of right (clockwise) torque in N·m. */
  tau2: number;
  /** Signed net torque in N·m (tau1 - tau2; positive = tips left/CCW, negative = tips right/CW). */
  netTorque: number;
  /** True when |netTorque| <= tolerance. */
  balanced: boolean;
  /** Tilt direction ("left", "right", or "level"). */
  tilt: TiltDirection;
  /** Ideal mechanical advantage = d_effort / d_load, or null when effortSide is omitted or d_load is 0. */
  mechanicalAdvantage: number | null;
};

function clampNonNegative(value: number, name: string): number {
  if (!Number.isFinite(value)) {
    throw new RangeError(`${name} must be a finite number`);
  }
  return Math.max(0, value);
}

/**
 * Computes weights, torques, net torque, balance state, tilt direction, and
 * optional ideal mechanical advantage for a horizontal first-class lever.
 */
export function computeLeverState(input: LeverInput): LeverState {
  const m1 = clampNonNegative(input.m1, "m1");
  const d1 = clampNonNegative(input.d1, "d1");
  const m2 = clampNonNegative(input.m2, "m2");
  const d2 = clampNonNegative(input.d2, "d2");
  const g = clampNonNegative(input.g ?? DEFAULT_GRAVITY, "g");
  const tolerance = clampNonNegative(input.tolerance ?? DEFAULT_BALANCE_TOLERANCE, "tolerance");

  const w1 = m1 * g;
  const w2 = m2 * g;
  const tau1 = w1 * d1;
  const tau2 = w2 * d2;
  const netTorque = tau1 - tau2;
  const balanced = Math.abs(netTorque) <= tolerance;
  const tilt: TiltDirection = balanced ? "level" : netTorque > 0 ? "left" : "right";

  let mechanicalAdvantage: number | null = null;
  if (input.effortSide === "left") {
    mechanicalAdvantage = d2 > 0 ? d1 / d2 : null;
  } else if (input.effortSide === "right") {
    mechanicalAdvantage = d1 > 0 ? d2 / d1 : null;
  }

  return {
    w1,
    w2,
    tau1,
    tau2,
    netTorque,
    balanced,
    tilt,
    mechanicalAdvantage,
  };
}

/**
 * Maps net torque to a visual beam tilt angle in degrees (clamped to [-maxDeg, +maxDeg]).
 * Negative rotation around +y tilts the left (-x) side downward; positive tilts the right (+x) side downward.
 */
export function targetTiltDegrees(state: LeverState, maxDeg = 10): number {
  // A rigid lever that is not in equilibrium keeps rotating until an end rests on the
  // ground, whatever the size of the net torque, so any imbalance shows the full tilt.
  if (state.balanced) return 0;
  return state.tilt === "left" ? -maxDeg : maxDeg;
}
