import Matter from "matter-js";
import {
  cartHeightMeters,
  cartWidthMeters,
  computeCollisionTheory,
  computeInstantaneousMetrics,
  computeTheoreticalImpactTime,
  INITIAL_CART1_POS_M,
  INITIAL_CART2_POS_M,
  TRACK_HALF_SPAN_M,
  type CollisionInput,
} from "./collisions";

export const MATTER_SCALE = 100; // 1 m = 100 Matter units
export const SIM_DT_MS = 1000 / 60;
export const SIM_DT_SEC = SIM_DT_MS / 1000;
export const VELOCITY_TO_MATTER = MATTER_SCALE * SIM_DT_SEC;
export const MAX_SIM_FRAMES = 900; // 15 s fixed horizon at 60 Hz
const STOPPED_DWELL_FRAMES = 30; // 0.5 s tail when both carts are stationary
const STOP_SPEED_EPS = 1e-4;

export type CollisionFrame = {
  /** Simulation time in seconds. */
  t: number;
  /** Cart 1 center position in meters. */
  x1: number;
  /** Cart 2 center position in meters. */
  x2: number;
  /** Cart 1 velocity in m/s. */
  v1: number;
  /** Cart 2 velocity in m/s. */
  v2: number;
  /** Cart 1 momentum in kg·m/s. */
  p1: number;
  /** Cart 2 momentum in kg·m/s. */
  p2: number;
  /** Total momentum (p1 + p2) in kg·m/s. */
  P: number;
  /** Cart 1 kinetic energy in J. */
  KE1: number;
  /** Cart 2 kinetic energy in J. */
  KE2: number;
  /** Total kinetic energy (KE1 + KE2) in J. */
  KE: number;
};

export type PrecomputedCollisionRun = {
  input: CollisionInput;
  frames: CollisionFrame[];
  dtSeconds: number;
  /** Index into `frames` where contact begins, or null if carts never collide on the track. */
  impactFrameIndex: number | null;
  /** Simulation time of the impact frame in seconds, or null. */
  impactTime: number | null;
  /** Analytical impact time (gap / closing speed) in seconds, or null if v1 <= v2. */
  theoreticalImpactTime: number | null;
  /** Contact x-position in meters at impact, or null. */
  impactX: number | null;
  /** Measured post-collision velocity of cart 1 in m/s, or null. */
  measuredV1After: number | null;
  /** Measured post-collision velocity of cart 2 in m/s, or null. */
  measuredV2After: number | null;
};

function makeFrame(
  t: number,
  x1: number,
  x2: number,
  v1: number,
  v2: number,
  m1: number,
  m2: number,
): CollisionFrame {
  const metrics = computeInstantaneousMetrics(m1, m2, v1, v2);
  return {
    t,
    x1,
    x2,
    v1,
    v2,
    p1: metrics.p1,
    p2: metrics.p2,
    P: metrics.totalP,
    KE1: metrics.ke1,
    KE2: metrics.ke2,
    KE: metrics.totalKe,
  };
}

/**
 * Pre-computes an entire 1D collision run in Matter.js using a fixed 60 Hz timestep
 * from t = 0 until either cart reaches a track end, both carts stop, or MAX_SIM_FRAMES.
 * Performs no DOM or rendering work.
 */
export function precomputeCollisionRun(input: CollisionInput): PrecomputedCollisionRun {
  const theory = computeCollisionTheory(input);
  const theoreticalImpactTime = computeTheoreticalImpactTime(input);

  // Disable resting-contact suppression so slow closing speeds preserve exact restitution e.
  (Matter.Resolver as unknown as { _restingThresh: number })._restingThresh = 0;

  const engine = Matter.Engine.create({
    gravity: { x: 0, y: 0, scale: 0 },
    positionIterations: 10,
    velocityIterations: 6,
  });

  const w1M = cartWidthMeters(theory.m1);
  const w2M = cartWidthMeters(theory.m2);
  const halfW1 = w1M / 2;
  const halfW2 = w2M / 2;

  const commonBodyOptions: Matter.IChamferableBodyDefinition = {
    friction: 0,
    frictionStatic: 0,
    frictionAir: 0,
    restitution: theory.e,
    slop: 0,
    inertia: Infinity,
  };

  const body1 = Matter.Bodies.rectangle(
    INITIAL_CART1_POS_M * MATTER_SCALE,
    0,
    w1M * MATTER_SCALE,
    cartHeightMeters(theory.m1) * MATTER_SCALE,
    { ...commonBodyOptions, label: "cart1" },
  );
  const body2 = Matter.Bodies.rectangle(
    INITIAL_CART2_POS_M * MATTER_SCALE,
    0,
    w2M * MATTER_SCALE,
    cartHeightMeters(theory.m2) * MATTER_SCALE,
    { ...commonBodyOptions, label: "cart2" },
  );

  Matter.Body.setMass(body1, theory.m1);
  Matter.Body.setInertia(body1, Infinity);
  Matter.Body.setMass(body2, theory.m2);
  Matter.Body.setInertia(body2, Infinity);

  Matter.Body.setVelocity(body1, { x: theory.v1 * VELOCITY_TO_MATTER, y: 0 });
  Matter.Body.setVelocity(body2, { x: theory.v2 * VELOCITY_TO_MATTER, y: 0 });

  Matter.Composite.add(engine.world, [body1, body2]);

  let currentStep = 0;
  let impactFrameIndex: number | null = null;
  let impactTime: number | null = null;
  let impactX: number | null = null;
  let postFrames = 0;
  let measuredV1After: number | null = null;
  let measuredV2After: number | null = null;

  Matter.Events.on(engine, "collisionStart", () => {
    if (impactFrameIndex === null) {
      impactFrameIndex = currentStep;
      impactTime = currentStep * SIM_DT_SEC;
      const rightEdge1 = body1.position.x / MATTER_SCALE + halfW1;
      const leftEdge2 = body2.position.x / MATTER_SCALE - halfW2;
      impactX = (rightEdge1 + leftEdge2) / 2;
    }
  });

  const frames: CollisionFrame[] = [
    makeFrame(0, INITIAL_CART1_POS_M, INITIAL_CART2_POS_M, theory.v1, theory.v2, theory.m1, theory.m2),
  ];

  for (currentStep = 1; currentStep <= MAX_SIM_FRAMES; currentStep += 1) {
    Matter.Engine.update(engine, SIM_DT_MS);

    // Enforce 1D track constraint strictly (no vertical drift or rotation).
    if (body1.position.y !== 0 || body1.angle !== 0) {
      Matter.Body.setPosition(body1, { x: body1.position.x, y: 0 });
      Matter.Body.setAngle(body1, 0);
    }
    if (body2.position.y !== 0 || body2.angle !== 0) {
      Matter.Body.setPosition(body2, { x: body2.position.x, y: 0 });
      Matter.Body.setAngle(body2, 0);
    }

    let x1 = body1.position.x / MATTER_SCALE;
    let x2 = body2.position.x / MATTER_SCALE;
    const v1 = body1.velocity.x / VELOCITY_TO_MATTER;
    const v2 = body2.velocity.x / VELOCITY_TO_MATTER;

    if (impactFrameIndex !== null) {
      postFrames += 1;
      if (postFrames === 1 || postFrames === 2) {
        measuredV1After = v1;
        measuredV2After = v2;
      }
    }

    const hitLeftBumper = x1 - halfW1 <= -TRACK_HALF_SPAN_M;
    const hitRightBumper = x2 + halfW2 >= TRACK_HALF_SPAN_M;
    if (hitLeftBumper) {
      x1 = -TRACK_HALF_SPAN_M + halfW1;
      Matter.Body.setPosition(body1, { x: x1 * MATTER_SCALE, y: 0 });
    }
    if (hitRightBumper) {
      x2 = TRACK_HALF_SPAN_M - halfW2;
      Matter.Body.setPosition(body2, { x: x2 * MATTER_SCALE, y: 0 });
    }

    frames.push(makeFrame(currentStep * SIM_DT_SEC, x1, x2, v1, v2, theory.m1, theory.m2));

    if (hitLeftBumper || hitRightBumper) {
      if (impactFrameIndex !== null && measuredV1After === null) {
        measuredV1After = v1;
        measuredV2After = v2;
      }
      break;
    }

    const bothStopped = Math.abs(v1) < STOP_SPEED_EPS && Math.abs(v2) < STOP_SPEED_EPS;
    if (impactFrameIndex !== null) {
      if (bothStopped && postFrames >= STOPPED_DWELL_FRAMES) break;
    } else if (!theory.willCollide && bothStopped && currentStep >= STOPPED_DWELL_FRAMES) {
      break;
    }
  }

  return {
    input: {
      m1: theory.m1,
      m2: theory.m2,
      v1: theory.v1,
      v2: theory.v2,
      e: theory.e,
    },
    frames,
    dtSeconds: SIM_DT_SEC,
    impactFrameIndex,
    impactTime,
    theoreticalImpactTime,
    impactX,
    measuredV1After,
    measuredV2After,
  };
}
