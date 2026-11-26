import assert from "node:assert/strict";
import { test } from "node:test";
import {
  computeCollisionTheory,
  computeInstantaneousMetrics,
  velocityErrorPercent,
} from "../src/lib/playground/collisions";

const approx = (actual: number, expected: number, eps = 1e-9) => {
  assert.ok(
    Math.abs(actual - expected) <= eps,
    `expected ${expected}, got ${actual} (diff ${Math.abs(actual - expected)})`,
  );
};

test("Elastic equal masses swap velocities and conserve both momentum and KE", () => {
  const res = computeCollisionTheory({ m1: 2, m2: 2, v1: 2, v2: 0, e: 1 });
  assert.equal(res.willCollide, true);
  assert.equal(res.collisionKind, "elastic");
  approx(res.v1After, 0);
  approx(res.v2After, 2);
  approx(res.pBefore, 4);
  approx(res.pAfter, 4);
  approx(res.keBefore, 4);
  approx(res.keAfter, 4);
  approx(res.keLost, 0);

  // Moving in opposite directions with equal masses also swaps velocities
  const headOn = computeCollisionTheory({ m1: 1.5, m2: 1.5, v1: 3, v2: -1.5, e: 1 });
  approx(headOn.v1After, -1.5);
  approx(headOn.v2After, 3);
  approx(headOn.pAfter, headOn.pBefore);
  approx(headOn.keAfter, headOn.keBefore);
  approx(headOn.keLost, 0);
});

test("Perfectly inelastic (e = 0) produces common velocity and maximizes KE loss", () => {
  const res = computeCollisionTheory({ m1: 1, m2: 4, v1: 2, v2: -1, e: 0 });
  assert.equal(res.willCollide, true);
  assert.equal(res.collisionKind, "perfectly-inelastic");
  // v' = (1*2 + 4*(-1)) / 5 = -2 / 5 = -0.4 m/s
  approx(res.v1After, -0.4);
  approx(res.v2After, -0.4);
  approx(res.pBefore, -2);
  approx(res.pAfter, -2);
  // KE before = 0.5*1*4 + 0.5*4*1 = 4 J; KE after = 0.5*5*0.16 = 0.4 J; lost = 3.6 J
  approx(res.keBefore, 4.0);
  approx(res.keAfter, 0.4);
  approx(res.keLost, 3.6);
});

test("Momentum is always conserved across all restitution values and unequal masses", () => {
  const restitutions = [0, 0.25, 0.5, 0.75, 1];
  for (const e of restitutions) {
    const res = computeCollisionTheory({ m1: 1.5, m2: 3.5, v1: 2.5, v2: -1.0, e });
    approx(res.pAfter, res.pBefore, 1e-12);
    if (e < 1) {
      assert.ok(res.keLost > 0, `expected KE loss for e=${e}`);
      approx(res.keBefore - res.keAfter, res.keLost, 1e-12);
    } else {
      approx(res.keLost, 0, 1e-12);
      approx(res.keAfter, res.keBefore, 1e-12);
    }
    // Check restitution definition: v2' - v1' = e * (v1 - v2)
    approx(res.v2After - res.v1After, e * (res.v1 - res.v2), 1e-12);
  }
});

test("Sign convention and unequal mass directions", () => {
  // Light cart hitting heavy stationary cart rebounds left (negative v1')
  const lightHitsHeavy = computeCollisionTheory({ m1: 1, m2: 3, v1: 2, v2: 0, e: 1 });
  approx(lightHitsHeavy.v1After, -1.0);
  approx(lightHitsHeavy.v2After, 1.0);
  assert.ok(lightHitsHeavy.v1After < 0);
  assert.ok(lightHitsHeavy.v2After > 0);
  approx(lightHitsHeavy.pAfter, lightHitsHeavy.pBefore);

  // Heavy cart hitting light stationary cart continues right (both positive)
  const heavyHitsLight = computeCollisionTheory({ m1: 4, m2: 1, v1: 2, v2: 0, e: 1 });
  approx(heavyHitsLight.v1After, 1.2);
  approx(heavyHitsLight.v2After, 3.2);
  assert.ok(heavyHitsLight.v1After > 0);
  assert.ok(heavyHitsLight.v2After > 0);
  approx(heavyHitsLight.pAfter, heavyHitsLight.pBefore);

  // Overtaking collision (both moving right, cart 1 faster than cart 2)
  const overtake = computeCollisionTheory({ m1: 2, m2: 3, v1: 3, v2: 1, e: 0.5 });
  // P = 6 + 3 = 9; v1' = (9 + 3*0.5*(1-3))/5 = 6/5 = 1.2; v2' = (9 + 2*0.5*(3-1))/5 = 11/5 = 2.2
  approx(overtake.v1After, 1.2);
  approx(overtake.v2After, 2.2);
  approx(overtake.pAfter, 9);
});

test("Non-colliding carts (v1 <= v2) report no-collision and keep initial velocities", () => {
  const apart = computeCollisionTheory({ m1: 2, m2: 2, v1: -1, v2: 1, e: 1 });
  assert.equal(apart.willCollide, false);
  assert.equal(apart.collisionKind, "no-collision");
  approx(apart.v1After, -1);
  approx(apart.v2After, 1);
  approx(apart.keLost, 0);

  const sameSpeed = computeCollisionTheory({ m1: 1, m2: 3, v1: 1.5, v2: 1.5, e: 0 });
  assert.equal(sameSpeed.willCollide, false);
  assert.equal(sameSpeed.collisionKind, "no-collision");
  approx(sameSpeed.keLost, 0);
});

test("Input validation and instantaneous metrics", () => {
  assert.throws(() => computeCollisionTheory({ m1: 0, m2: 2, v1: 1, v2: 0, e: 1 }), RangeError);
  assert.throws(() => computeCollisionTheory({ m1: 2, m2: 2, v1: 1, v2: 0, e: 1.2 }), RangeError);
  assert.throws(() => computeCollisionTheory({ m1: 2, m2: 2, v1: Number.NaN, v2: 0, e: 1 }), RangeError);

  const inst = computeInstantaneousMetrics(2, 3, -1.5, 2.0);
  approx(inst.p1, -3);
  approx(inst.p2, 6);
  approx(inst.totalP, 3);
  approx(inst.ke1, 2.25);
  approx(inst.ke2, 6);
  approx(inst.totalKe, 8.25);

  approx(velocityErrorPercent(2.0, 2.0), 0);
  approx(velocityErrorPercent(2.01, 2.0), 0.5);
});
