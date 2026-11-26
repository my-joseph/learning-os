import assert from "node:assert/strict";
import { test } from "node:test";
import {
  computeDiskMethod,
  computePresetDiskMethod,
  DISK_PRESETS,
} from "../src/lib/isometric/math/diskMethod";

const TOL = 1e-9;

test("Preset exact closed-form volumes match analytical calculus values", () => {
  assert.ok(Math.abs(DISK_PRESETS.sqrt.exactVolume - 8 * Math.PI) < TOL);
  assert.ok(Math.abs(DISK_PRESETS.cone.exactVolume - 9 * Math.PI) < TOL);
  assert.ok(Math.abs(DISK_PRESETS.sine.exactVolume - (Math.PI * Math.PI) / 2) < TOL);
});

test("Approx volume converges to exact volume as n grows across presets", () => {
  // f(x) = sqrt(x) on [0, 4]: [f(x)]^2 = x is linear, so midpoint is exact for all n >= 1,
  // while left and right errors decrease strictly monotonically as 8*pi/n.
  for (const n of [1, 4, 10, 20, 40]) {
    const mid = computePresetDiskMethod("sqrt", n, "midpoint");
    assert.equal(mid.absoluteError, 0);
    assert.equal(mid.relativeError, 0);
  }
  const sqrtLeftErrors = [4, 10, 20, 40].map(
    (n) => computePresetDiskMethod("sqrt", n, "left").absoluteError!,
  );
  for (let i = 1; i < sqrtLeftErrors.length; i++) {
    assert.ok(
      sqrtLeftErrors[i] < sqrtLeftErrors[i - 1],
      `Expected sqrt left error to decrease: ${sqrtLeftErrors}`,
    );
  }
  assert.ok(sqrtLeftErrors[sqrtLeftErrors.length - 1] < 0.7);

  // f(x) = x on [0, 3]: [f(x)]^2 = x^2 is quadratic, so midpoint, left, and right
  // errors all decrease strictly monotonically at n = 10, 20, 40.
  for (const rule of ["left", "midpoint", "right"] as const) {
    const errors = [10, 20, 40].map(
      (n) => computePresetDiskMethod("cone", n, rule).absoluteError!,
    );
    assert.ok(
      errors[1] < errors[0] && errors[2] < errors[1],
      `Expected cone ${rule} error to decrease strictly: ${errors}`,
    );
  }
  const coneMid40 = computePresetDiskMethod("cone", 40, "midpoint");
  assert.ok(coneMid40.relativeError! < 0.0005);

  // f(x) = sin(x) on [0, pi]: exact for n >= 2 (periodic sin^2 x), large error at n = 1.
  const sineMid1 = computePresetDiskMethod("sine", 1, "midpoint");
  const sineMid10 = computePresetDiskMethod("sine", 10, "midpoint");
  assert.ok(sineMid1.absoluteError! > 4);
  assert.equal(sineMid10.absoluteError, 0);

  // Non-polynomial custom curve f(x) = sqrt(x^3) => [f(x)]^2 = x^3 on [0, 2], exact = 4*pi.
  const exactCubic = 4 * Math.PI;
  const cubicMidErrors = [10, 20, 40].map(
    (n) => computeDiskMethod((x) => Math.sqrt(x ** 3), 0, 2, n, "midpoint", exactCubic).absoluteError!,
  );
  assert.ok(cubicMidErrors[1] < cubicMidErrors[0] && cubicMidErrors[2] < cubicMidErrors[1]);
});

test("Left < exact < right ordering holds for strictly increasing non-negative functions", () => {
  for (const presetId of ["sqrt", "cone"] as const) {
    for (const n of [1, 4, 12, 40]) {
      const left = computePresetDiskMethod(presetId, n, "left");
      const mid = computePresetDiskMethod(presetId, n, "midpoint");
      const right = computePresetDiskMethod(presetId, n, "right");
      assert.ok(
        left.approxVolume < left.exactVolume! && left.exactVolume! < right.approxVolume,
        `Expected L < exact < R for ${presetId} n=${n}: L=${left.approxVolume}, exact=${left.exactVolume}, R=${right.approxVolume}`,
      );
      assert.ok(
        mid.absoluteError! <= left.absoluteError! && mid.absoluteError! <= right.absoluteError!,
        `Expected midpoint to be at least as accurate as endpoints for ${presetId} n=${n}`,
      );
    }
  }
});

test("n = 1 edge case produces one valid disk spanning [a, b]", () => {
  const sqrtLeft = computePresetDiskMethod("sqrt", 1, "left");
  assert.equal(sqrtLeft.disks.length, 1);
  assert.equal(sqrtLeft.dx, 4);
  assert.equal(sqrtLeft.disks[0].x, 0);
  assert.equal(sqrtLeft.disks[0].r, 0);
  assert.equal(sqrtLeft.disks[0].volume, 0);
  assert.equal(sqrtLeft.approxVolume, 0);

  const sqrtRight = computePresetDiskMethod("sqrt", 1, "right");
  assert.equal(sqrtRight.disks.length, 1);
  assert.equal(sqrtRight.disks[0].x, 4);
  assert.equal(sqrtRight.disks[0].r, 2);
  assert.ok(Math.abs(sqrtRight.approxVolume - 16 * Math.PI) < TOL);

  const coneMid = computePresetDiskMethod("cone", 1, "midpoint");
  assert.equal(coneMid.disks.length, 1);
  assert.equal(coneMid.disks[0].x, 1.5);
  assert.equal(coneMid.disks[0].r, 1.5);
  assert.ok(Math.abs(coneMid.approxVolume - Math.PI * 1.5 * 1.5 * 3) < TOL);

  const sineMid = computePresetDiskMethod("sine", 1, "midpoint");
  assert.equal(sineMid.disks.length, 1);
  assert.ok(Math.abs(sineMid.approxVolume - Math.PI * Math.PI) < TOL);
});

test("computeDiskMethod rejects invalid n or inverted bounds", () => {
  assert.throws(() => computeDiskMethod((x) => x, 0, 3, 0, "midpoint"), RangeError);
  assert.throws(() => computeDiskMethod((x) => x, 0, 3, 2.5, "midpoint"), RangeError);
  assert.throws(() => computeDiskMethod((x) => x, 3, 3, 4, "midpoint"), RangeError);
  assert.throws(() => computeDiskMethod((x) => x, 4, 1, 4, "midpoint"), RangeError);
});
