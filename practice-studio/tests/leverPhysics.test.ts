import assert from "node:assert/strict";
import { test } from "node:test";
import {
  computeLeverState,
  DEFAULT_GRAVITY,
  targetTiltDegrees,
} from "../src/lib/isometric/physics/lever";

test("Equilibrium: 20 kg at 1.0 m balances 10 kg at 2.0 m", () => {
  const result = computeLeverState({
    m1: 20,
    d1: 1.0,
    m2: 10,
    d2: 2.0,
  });

  // Weights in Newtons (W = m * g)
  assert.ok(Math.abs(result.w1 - 20 * 9.8) < 1e-9);
  assert.ok(Math.abs(result.w2 - 10 * 9.8) < 1e-9);

  // Torques in N·m (tau = W * d)
  assert.ok(Math.abs(result.tau1 - 196.0) < 1e-9);
  assert.ok(Math.abs(result.tau2 - 196.0) < 1e-9);
  assert.ok(Math.abs(result.netTorque) < 1e-9);

  assert.equal(result.balanced, true);
  assert.equal(result.tilt, "level");
  assert.equal(result.mechanicalAdvantage, null);
  assert.equal(targetTiltDegrees(result), 0);
});

test("Imbalance direction: tips left when left torque exceeds right torque", () => {
  const result = computeLeverState({
    m1: 20,
    d1: 1.5,
    m2: 10,
    d2: 1.5,
  });

  assert.ok(Math.abs(result.tau1 - 294.0) < 1e-9);
  assert.ok(Math.abs(result.tau2 - 147.0) < 1e-9);
  assert.ok(Math.abs(result.netTorque - 147.0) < 1e-9);
  assert.equal(result.balanced, false);
  assert.equal(result.tilt, "left");
  assert.ok(targetTiltDegrees(result) < 0);
});

test("Imbalance direction: tips right when right torque exceeds left torque", () => {
  const result = computeLeverState({
    m1: 10,
    d1: 1.0,
    m2: 15,
    d2: 2.0,
  });

  assert.ok(Math.abs(result.tau1 - 98.0) < 1e-9);
  assert.ok(Math.abs(result.tau2 - 294.0) < 1e-9);
  assert.ok(Math.abs(result.netTorque - -196.0) < 1e-9);
  assert.equal(result.balanced, false);
  assert.equal(result.tilt, "right");
  assert.ok(targetTiltDegrees(result) > 0);
});

test("Zero-distance edge case: load at fulcrum exerts zero torque", () => {
  const oneZero = computeLeverState({
    m1: 30,
    d1: 0,
    m2: 5,
    d2: 1.0,
  });
  assert.ok(Math.abs(oneZero.w1 - 294.0) < 1e-9);
  assert.equal(oneZero.tau1, 0);
  assert.ok(Math.abs(oneZero.tau2 - 49.0) < 1e-9);
  assert.equal(oneZero.balanced, false);
  assert.equal(oneZero.tilt, "right");

  const bothZero = computeLeverState({
    m1: 25,
    d1: 0,
    m2: 10,
    d2: 0,
  });
  assert.equal(bothZero.tau1, 0);
  assert.equal(bothZero.tau2, 0);
  assert.equal(bothZero.netTorque, 0);
  assert.equal(bothZero.balanced, true);
  assert.equal(bothZero.tilt, "level");
});

test("Mechanical advantage: MA = d_effort / d_load and null when load arm is 0", () => {
  const leftEffort = computeLeverState({
    m1: 10,
    d1: 2.0,
    m2: 20,
    d2: 1.0,
    effortSide: "left",
  });
  assert.equal(leftEffort.mechanicalAdvantage, 2.0);

  const rightEffort = computeLeverState({
    m1: 20,
    d1: 1.0,
    m2: 10,
    d2: 2.0,
    effortSide: "right",
  });
  assert.equal(rightEffort.mechanicalAdvantage, 2.0);

  const zeroLoadArm = computeLeverState({
    m1: 10,
    d1: 1.5,
    m2: 20,
    d2: 0,
    effortSide: "left",
  });
  assert.equal(zeroLoadArm.mechanicalAdvantage, null);
});

test("Units and custom gravity: forces in N (m * g) and torques in N·m (W * d)", () => {
  assert.equal(DEFAULT_GRAVITY, 9.8);
  const custom = computeLeverState({
    m1: 10,
    d1: 1.5,
    m2: 10,
    d2: 1.5,
    g: 10,
  });
  assert.equal(custom.w1, 100);
  assert.equal(custom.w2, 100);
  assert.equal(custom.tau1, 150);
  assert.equal(custom.tau2, 150);
  assert.equal(custom.balanced, true);
});

test("Balance tolerance and tilt angle clamping", () => {
  const withinTol = computeLeverState({
    m1: 10,
    d1: 1.0,
    m2: 10,
    d2: 1.0005,
    tolerance: 0.05,
  });
  assert.equal(withinTol.balanced, true);
  assert.equal(withinTol.tilt, "level");

  const huge = computeLeverState({
    m1: 100,
    d1: 2.0,
    m2: 5,
    d2: 0.5,
  });
  assert.equal(targetTiltDegrees(huge, 10), -10);
});
