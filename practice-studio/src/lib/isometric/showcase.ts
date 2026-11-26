/** A demo supplies spring targets. The caller owns the springs and the figure's normal inputs. */
export type ShowcaseScript = {
  defaults(): void
  /** Seconds of visible playback. Return true when a target or a discrete input changes. */
  play(seconds: number): boolean
}

export const SHOWCASE_RETURN_SECONDS = 0.55
export const SHOWCASE_IDLE_SECONDS = 2

export function easeInOut(progress: number) {
  const t = Math.min(1, Math.max(0, progress))
  return t * t * (3 - 2 * t)
}

type Phase = "playing" | "returning" | "engaged" | "waiting" | "held" | "reduced"

/** The shared frame clock supplies elapsed time. No wall clock runs while the stage sleeps. */
export function createShowcaseController(keepEdits: boolean, restore: () => void) {
  let engaged = false
  let edited = false
  let reduced = false
  let phase: Phase = "playing"
  let elapsed = 0

  function start(next: Phase) {
    phase = next
    elapsed = 0
  }

  function reset() {
    edited = false
    restore()
    start(reduced ? "reduced" : engaged ? "returning" : "waiting")
  }

  return {
    get phase() { return phase },
    get playhead() { return elapsed },
    get announce() { return engaged && (phase === "engaged" || phase === "held" || phase === "reduced") },
    engage(active: boolean) {
      if (engaged === active) return
      engaged = active
      if (reduced || (keepEdits && edited)) return
      if (active || phase === "engaged") restore()
      if (!active) edited = false
      start(active ? "returning" : "waiting")
    },
    change() {
      edited = true
      if (!reduced) start(keepEdits ? "held" : "engaged")
    },
    reset,
    tick(dt: number, reduce: boolean) {
      if (reduce !== reduced) {
        reduced = reduce
        if (keepEdits && edited) {
          start(reduced ? "reduced" : "held")
        } else {
          reset()
        }
      }
      elapsed += dt
      if (phase === "returning" && elapsed >= SHOWCASE_RETURN_SECONDS) start("engaged")
      if (phase === "waiting" && elapsed >= SHOWCASE_IDLE_SECONDS) start("playing")
      return phase === "playing" || phase === "waiting" || phase === "returning"
    },
  }
}
