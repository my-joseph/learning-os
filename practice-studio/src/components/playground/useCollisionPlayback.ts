import { useCallback, useEffect, useRef, useState } from "react";
import { reducedMotion } from "@/lib/isometric/motion";
import { easeInOut, SHOWCASE_RETURN_SECONDS } from "@/lib/isometric/showcase";
import { resetShowcase, showcaseLoop } from "@/lib/isometric/showcaseStage";
import { DEFAULT_COLLISION_INPUT, normalizeCollisionPositions, type CollisionInput } from "@/lib/playground/collisions";
import {
  createCollisionShowcase,
  precomputeCollisionRun,
  type CollisionFrame,
  type PrecomputedCollisionRun,
} from "@/lib/playground/collisionsSim";

type Pose = Pick<CollisionFrame, "x1" | "x2" | "v1" | "v2">;
type Playback = { run: PrecomputedCollisionRun; frameIndex: number; playing: boolean; pose?: Pose };

function blendPose(from: Pose, to: Pose, t: number): Pose {
  return {
    x1: from.x1 + (to.x1 - from.x1) * t,
    x2: from.x2 + (to.x2 - from.x2) * t,
    v1: from.v1 + (to.v1 - from.v1) * t,
    v2: from.v2 + (to.v2 - from.v2) * t,
  };
}

export function useCollisionPlayback() {
  const stageRef = useRef<HTMLDivElement>(null);
  const stageLoop = useRef<ReturnType<typeof showcaseLoop> | null>(null);
  const [defaults] = useState(() => precomputeCollisionRun(DEFAULT_COLLISION_INPUT));
  const [selectedCart, setSelectedCart] = useState<1 | 2>(1);
  const [state, setState] = useState<Playback>({ run: defaults, frameIndex: 0, playing: false });
  const current = useRef(state);
  const manual = useRef<{ start: number; elapsed: number } | null>(null);
  const glide = useRef<{ from: Pose; elapsed: number; duration: number } | null>(null);

  const publish = useCallback((next: Playback) => {
    current.current = next;
    setState(next);
  }, []);

  useEffect(() => {
    const stage = stageRef.current;
    if (!stage) return;
    let demo: ReturnType<typeof createCollisionShowcase> | undefined;

    const moveToStart = (run: PrecomputedCollisionRun, duration: number) => {
      const prev = current.current;
      const from = prev.pose ?? prev.run.frames[prev.frameIndex];
      const to = run.frames[0];
      const moves = !reducedMotion() && (from.x1 !== to.x1 || from.x2 !== to.x2 ||
        from.v1 !== to.v1 || from.v2 !== to.v2);
      manual.current = null;
      glide.current = moves ? { from, elapsed: 0, duration } : null;
      publish({ run, frameIndex: 0, playing: false, pose: moves ? from : undefined });
    };

    const handle = showcaseLoop(stage, (dt) => {
      const prev = current.current;
      if (glide.current) {
        const transition = glide.current;
        transition.elapsed += dt;
        const progress = transition.elapsed / transition.duration;
        if (progress >= 1 || reducedMotion()) {
          glide.current = null;
          publish({ ...prev, pose: undefined });
        } else {
          publish({ ...prev, pose: blendPose(transition.from, prev.run.frames[0], easeInOut(progress)) });
        }
        return glide.current !== null;
      }
      const playback = manual.current;
      if (!playback) return false;
      playback.elapsed += dt;
      const last = prev.run.frames.length - 1;
      const frameIndex = reducedMotion() ? last : Math.min(last, playback.start + Math.floor(playback.elapsed / prev.run.dtSeconds));
      if (frameIndex === last) manual.current = null;
      if (frameIndex !== prev.frameIndex || manual.current === null) {
        publish({ run: prev.run, frameIndex, playing: manual.current !== null });
      }
      return manual.current !== null;
    }, {
      defaults() {
        moveToStart(defaults, SHOWCASE_RETURN_SECONDS);
      },
      play(seconds) {
        demo ??= createCollisionShowcase(defaults);
        const next = demo.at(seconds);
        const prev = current.current;
        if (next.run !== prev.run || manual.current) {
          moveToStart(next.run, 0.45);
          return true;
        }
        if (next.frameIndex === prev.frameIndex && next.playing === prev.playing) return false;
        if (next.playing) glide.current = null;
        publish(next);
        return true;
      },
    });

    stageLoop.current = handle;
    return () => {
      stageLoop.current = null;
      handle.stop();
    };
  }, [defaults, publish]);

  const markEdit = useCallback(() => {
    glide.current = null;
    stageLoop.current?.change();
  }, []);

  const startPlayback = useCallback((run: PrecomputedCollisionRun, start: number) => {
    const reduce = reducedMotion();
    manual.current = reduce ? null : { start, elapsed: 0 };
    publish({ run, frameIndex: reduce ? run.frames.length - 1 : start, playing: !reduce });
    stageLoop.current?.wake();
  }, [publish]);

  const seek = useCallback((frameIndex: number) => {
    markEdit();
    manual.current = null;
    publish({ run: current.current.run, frameIndex, playing: false });
  }, [markEdit, publish]);

  const togglePlayback = useCallback(() => {
    if (manual.current) {
      seek(current.current.frameIndex);
      return;
    }
    markEdit();
    const { run, frameIndex } = current.current;
    startPlayback(run, frameIndex === run.frames.length - 1 ? 0 : frameIndex);
  }, [markEdit, seek, startPlayback]);

  const changeInput = useCallback((input: CollisionInput, autoPlay = false) => {
    markEdit();
    const run = precomputeCollisionRun(normalizeCollisionPositions(input));
    if (autoPlay) {
      startPlayback(run, 0);
    } else {
      manual.current = null;
      publish({ run, frameIndex: 0, playing: false });
    }
  }, [markEdit, publish, startPlayback]);

  const reset = useCallback(() => {
    setSelectedCart(1);
    if (stageRef.current) resetShowcase(stageRef.current);
  }, []);

  return { ...state, stageRef, selectedCart, setSelectedCart, seek, togglePlayback, changeInput, reset };
}
