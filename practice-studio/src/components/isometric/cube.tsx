"use client"

/*
 * Copyright (c) 2026 Abhishek Mallick (MIT License)
 * Portions Copyright (c) 2026 Lucas Marques
 * Source: https://github.com/Abhishek-Mallick/Isometric
 */

import { createFigure } from "@/lib/isometric/figure"
import {
  camera,
  clamp,
  corners,
  deg,
  facing,
  fit,
  line,
  prism,
  project,
  roundRect,
  turn,
  type Projector,
  type Ring,
  type Sample,
  type Shape,
} from "@/lib/isometric/iso"
import { spring, step } from "@/lib/isometric/motion"
import { easeInOut } from "@/lib/isometric/showcase"
import { showcaseLoop } from "@/lib/isometric/showcaseStage"
import { bag, draw, el, pointer, solid, type Mount, type Solid } from "@/lib/isometric/stage"

/**
 * Cube — a three by three by three cube of cubelets. The pointer's height
 * picks a layer, which lifts a little; moving across twists it, and when the
 * pointer leaves it settles on the nearest quarter turn. `intensity` lets a
 * sweep across twist it further.
 */

const U = 19,
  G = 1.6,
  PITCH = U + G,
  SIDE = 3 * PITCH - G,
  MID = SIDE / 2,
  LIFT = 5
const NAMES = ["bottom", "middle", "top"]

/** A cubelet: a prism with a bevel, plus the one vertical edge nearest the camera. */
function cubelet(P: Projector, front: (q: Sample) => boolean, ring: Ring, bevel: Ring, z0: number, z1: number): Shape {
  const s = prism(P, front, ring, bevel, z0, z1)
  let near = ring[0],
    ny = -Infinity
  for (const q of ring) {
    const y = P(q.u, q.v, z0)[1]
    if (y > ny) {
      ny = y
      near = q
    }
  }
  return { outline: s.outline, inner: s.inner + line(P(near.u, near.v, z1), P(near.u, near.v, z0)) }
}

type Piece = { layer: number; ring: Ring; bevel: Ring; el: Solid; depth: number }

const mount: Mount<object> = ({ stage, svg, read }, maxTwist) => {
  const b = bag()
  const c = camera(45, 0.5, 2.05)
  fit(c, corners(-6, -6, SIDE + 6, SIDE + 6, 0, SIDE + LIFT), 200, 162)
  const P = project(c),
    front = facing(c)
  let top = maxTwist
  let pick = -1
  const twist = spring(0, 110, 16, 0.05)
  const lifts = [0, 1, 2].map(() => spring(0, 160, 20, 0.02))

  const g = el("g", null, svg)
  const groups = [0, 1, 2].map(() => el("g", null, g))
  const pieces: Piece[] = []
  for (let layer = 0; layer < 3; layer++) {
    for (let i = 0; i < 3; i++)
      for (let j = 0; j < 3; j++) {
        const x0 = i * PITCH,
          y0 = j * PITCH
        pieces.push({
          layer,
          ring: roundRect(x0, y0, x0 + U, y0 + U, 1.6),
          bevel: roundRect(x0 + 1.4, y0 + 1.4, x0 + U - 1.4, y0 + U - 1.4, 0.6),
          el: solid(groups[layer]),
          depth: 0,
        })
      }
  }

  let held = -1
  let demonstrating = false
  const L = showcaseLoop(stage, (dt) => {
    let moving = step(twist, dt)
    for (const l of lifts) if (step(l, dt)) moving = true
    for (let layer = 0; layer < 3; layer++) {
      const a = layer === pick || (pick < 0 && layer === held) ? deg(twist.x) : 0
      // a lifted layer opens a gap below it and carries the layers above it up twice as far
      let z0 = layer * PITCH + lifts[layer].x
      for (let k = 0; k < layer; k++) z0 += 2 * lifts[k].x
      const list = pieces.filter((p) => p.layer === layer)
      for (const p of list) {
        const ring = a ? turn(p.ring, a, MID, MID) : p.ring
        const bevel = a ? turn(p.bevel, a, MID, MID) : p.bevel
        const cu = ring.reduce((s, q) => s + q.u, 0) / ring.length,
          cv = ring.reduce((s, q) => s + q.v, 0) / ring.length
        p.depth = P(cu, cv, 0)[1]
        draw(p.el, cubelet(P, front, ring, bevel, z0, z0 + U))
        p.el.g.classList.toggle("accent", layer === pick)
      }
      // repaint this layer back to front: a twist changes which cubelet is nearest
      list.sort((m, n) => m.depth - n.depth).forEach((p) => groups[layer].appendChild(p.el.g))
    }
    // a settled quarter turn looks the same as none, so fold it away
    if (!moving && pick < 0 && held >= 0 && (!demonstrating || (twist.to === 0 && lifts.every((lift) => lift.to === 0)))) {
      twist.x = twist.to = 0
      held = -1
    }
    if (demonstrating) {
      read.textContent = held < 0 ? "cube" : `${NAMES[held]} · ${Math.round(twist.x)}°`
    }
    return moving
  }, {
    defaults() {
      demonstrating = true
      pick = -1
      twist.to = 0
      lifts.forEach((lift) => { lift.to = 0 })
    },
    play(seconds) {
      const slot = 3.4
      const phase = Math.floor(seconds / slot)
      const t = seconds % slot
      // Raise one layer, then twist it. Centre it before closing the gap.
      const lift = LIFT * easeInOut(t / 0.85) * easeInOut((2.95 - t) / 0.8)
      const turn = (phase % 3 === 1 ? -18 : 18) * easeInOut((t - 0.45) / 0.9) * easeInOut((2.45 - t) / 0.75)
      const layer = [2, 1, 0][phase % 3]
      if (lift === 0 && held < 0 && t > 0.85) return false
      const changed = held !== layer || twist.to !== turn || lifts[layer].to !== lift
      demonstrating = true
      held = layer
      twist.to = turn
      lifts.forEach((l, k) => { l.to = k === layer ? lift : 0 })
      return changed
    },
  })
  b.add(L.stop)

  // the screen height of each layer's middle, for picking by the pointer's height
  const ys = [0, 1, 2].map((k) => P(SIDE, SIDE, k * PITCH + U / 2)[1])

  b.add(
    pointer(stage, {
      move: (p) => {
        if (L.returning()) return
        demonstrating = false
        let best = 0
        ys.forEach((y, k) => {
          if (Math.abs(y - p[1]) < Math.abs(ys[best] - p[1])) best = k
        })
        if (best !== pick && pick >= 0) twist.x = twist.to = 0
        pick = best
        held = best
        twist.to = clamp((p[0] - 200) / 170, -1, 1) * top
        lifts.forEach((l, k) => {
          l.to = k === best ? LIFT : 0
        })
        read.textContent = `${NAMES[best]} · ${Math.round(twist.to)}°`
        L.wake()
      },
      leave: () => {
        if (pick < 0) return
        pick = -1
        twist.to = Math.round(twist.x / 90) * 90
        lifts.forEach((l) => {
          l.to = 0
        })
        read.textContent = "cube"
        L.wake()
      },
    }),
  )
  b.add(() => svg.replaceChildren())

  return {
    set: (v) => {
      top = v
    },
    destroy: b.dispose,
  }
}

export const Cube = createFigure("Cube", {
  id: "cube",
  label: "A three by three cube; the pointer's height picks a layer and moving across twists it.",
  rest: "cube",
  range: [45, 90, 180],
  focusable: true,
  defaults: {},
  mount,
})
