"use client"

// Practice Studio interactive Lever figure using the MIT-licensed Isometric engine (@/lib/isometric/*).

import { frame } from "@/lib/isometric/entity"
import { createFigure } from "@/lib/isometric/figure"
import { clamp, deg, unproject, type Vec2, type Vec3 } from "@/lib/isometric/iso"
import { box, cylinder, extrude, rotateX, rotateY, translate, type Mesh } from "@/lib/isometric/mesh"
import { showcaseSpring, spring, step, type Spring } from "@/lib/isometric/motion"
import {
  computeLeverState,
  DEFAULT_GRAVITY,
  LEVER_BEAM_HALF_SPAN,
  LEVER_MASS_PRESETS,
  LEVER_TICK_STEP,
  targetTiltDegrees,
  type LeverState,
} from "@/lib/isometric/physics/lever"
import { label, scene, type Item } from "@/lib/isometric/scene"
import { easeInOut } from "@/lib/isometric/showcase"
import { showcaseLoop } from "@/lib/isometric/showcaseStage"
import { bag, el, pointer, type Mount } from "@/lib/isometric/stage"

export type LeverProps = {
  /** Initial left load mass in kg. */
  leftMass?: number
  /** Initial right load mass in kg. */
  rightMass?: number
  /** Initial left load position along the beam in m (-2.0 to 2.0). */
  leftPos?: number
  /** Initial right load position along the beam in m (-2.0 to 2.0). */
  rightPos?: number
  /** Initial fulcrum position along the beam in m (-1.5 to 1.5). */
  fulcrumPos?: number
  /** Gravitational acceleration in m/s^2 (default 9.8). */
  gravity?: number
}

type PartId = "left-load" | "fulcrum" | "right-load"

const UNIT = 18 // 1 m = 18 world units
const BEAM_HALF_M = 2.35
const BEAM_HALF_W = BEAM_HALF_M * UNIT
const BASE_HALF_W = 2.45 * UNIT
const PIVOT_Z = 18
const BEAM_THICK = 3
const BEAM_TOP_Z = PIVOT_Z + BEAM_THICK
const FULCRUM_LIMIT_M = 1.5
const MIN_ARM_M = LEVER_TICK_STEP
const MAX_TILT_DEG = 12

const PART_NAMES: Record<PartId, string> = {
  "left-load": "Left load",
  fulcrum: "Fulcrum",
  "right-load": "Right load",
}

type Inputs = {
  leftMass: number
  rightMass: number
  leftM: number
  rightM: number
  fulcrumM: number
}

type State = Inputs & {
  g: number
  tiltDeg: Spring
  physics: LeverState
}

const round1 = (n: number) => Math.round(n * 10) / 10
const snapTick = (n: number) => Math.round(n / LEVER_TICK_STEP) * LEVER_TICK_STEP

function nextMassPreset(current: number): number {
  const idx = LEVER_MASS_PRESETS.indexOf(current as (typeof LEVER_MASS_PRESETS)[number])
  if (idx >= 0) return LEVER_MASS_PRESETS[(idx + 1) % LEVER_MASS_PRESETS.length]
  return LEVER_MASS_PRESETS.find((m) => m > current) ?? LEVER_MASS_PRESETS[0]
}

function rotatePointY(p: Vec3, a: number, pivot: Vec3): Vec3 {
  if (!a) return p
  const c = Math.cos(a)
  const s = Math.sin(a)
  const dx = p[0] - pivot[0]
  const dy = p[1] - pivot[1]
  const dz = p[2] - pivot[2]
  return [pivot[0] + dx * c + dz * s, pivot[1] + dy, pivot[2] - dx * s + dz * c]
}

function loadDimensions(massKg: number): [number, number, number] {
  const ratio = clamp((massKg - 5) / 25, 0, 1)
  return [3.1 + ratio * 1.3, 3.0 + ratio * 0.9, 5.4 + ratio * 5.2]
}

function fulcrumPrism(cx: number): Mesh {
  const wedge = extrude(
    [
      [-5.2, 0],
      [5.2, 0],
      [0, PIVOT_Z - 4.5],
    ],
    -4.5,
    4.5,
  )
  return translate(rotateX(wedge, Math.PI / 2), [cx, 0, 4.5])
}

function computePhysics(s: Pick<State, "leftMass" | "rightMass" | "leftM" | "rightM" | "fulcrumM" | "g">): LeverState {
  return computeLeverState({
    m1: s.leftMass,
    d1: Math.max(0, round1(s.fulcrumM - s.leftM)),
    m2: s.rightMass,
    d2: Math.max(0, round1(s.rightM - s.fulcrumM)),
    g: s.g,
  })
}

function formatSummary(s: State): string {
  const d1 = Math.max(0, round1(s.fulcrumM - s.leftM))
  const d2 = Math.max(0, round1(s.rightM - s.fulcrumM))
  const status = s.physics.balanced ? "Balanced" : s.physics.tilt === "left" ? "Tips left" : "Tips right"
  return `L ${s.leftMass} kg @ ${d1.toFixed(1)} m (${s.physics.tau1.toFixed(0)} N·m) · R ${s.rightMass} kg @ ${d2.toFixed(1)} m (${s.physics.tau2.toFixed(0)} N·m) · ${status}`
}

function stepByTick(current: number, dir: -1 | 1, min: number, max: number): number {
  const raw = dir < 0 ? Math.floor(current / LEVER_TICK_STEP - 1e-6) * LEVER_TICK_STEP : Math.ceil(current / LEVER_TICK_STEP + 1e-6) * LEVER_TICK_STEP
  return clamp(round1(snapTick(raw)), min, max)
}

const mount: Mount<LeverProps> = ({ stage, svg, read, activated, debug }, _value, props) => {
  const b = bag()
  const cam = frame({
    az: 8,
    k: 0.5,
    zoom: 0.96,
    fit: [
      [-BASE_HALF_W, -9, 0],
      [BASE_HALF_W, 9, 0],
      [-BASE_HALF_W, -9, 40],
      [BASE_HALF_W, 9, 40],
    ],
  })
  const sc = scene(el("g", null, svg), { debug })

  const initialFulcrum = clamp(round1(props.fulcrumPos ?? 0), -FULCRUM_LIMIT_M, FULCRUM_LIMIT_M)
  const initialLeft = clamp(round1(props.leftPos ?? -1.5), -LEVER_BEAM_HALF_SPAN, initialFulcrum - MIN_ARM_M)
  const initialRight = clamp(round1(props.rightPos ?? 1.5), initialFulcrum + MIN_ARM_M, LEVER_BEAM_HALF_SPAN)
  const initialG = props.gravity ?? DEFAULT_GRAVITY

  const state: State = {
    leftMass: props.leftMass ?? 20,
    rightMass: props.rightMass ?? 10,
    leftM: initialLeft,
    rightM: initialRight,
    fulcrumM: initialFulcrum,
    g: initialG,
    tiltDeg: spring(0, 95, 13, 0.02),
    physics: computeLeverState({
      m1: props.leftMass ?? 20,
      d1: round1(initialFulcrum - initialLeft),
      m2: props.rightMass ?? 10,
      d2: round1(initialRight - initialFulcrum),
      g: initialG,
    }),
  }
  const defaults: Inputs = { leftMass: state.leftMass, rightMass: state.rightMass, leftM: initialLeft, rightM: initialRight, fulcrumM: initialFulcrum }
  const inputKeys = Object.keys(defaults) as (keyof Inputs)[]
  const inputs = Object.fromEntries(inputKeys.map((key) => [key, showcaseSpring(defaults[key], 0.004)])) as Record<keyof Inputs, Spring>
  const poses: Inputs[] = [
    defaults,
    { leftMass: 15, rightMass: 15, leftM: -1, rightM: 1, fulcrumM: 0 },
    { leftMass: 10, rightMass: 25, leftM: -0.8, rightM: 1.8, fulcrumM: 0 },
    { leftMass: 20, rightMass: 10, leftM: -0.5, rightM: 1, fulcrumM: 0 },
  ]

  const initialTilt = targetTiltDegrees(state.physics, MAX_TILT_DEG)
  state.tiltDeg.x = initialTilt
  state.tiltDeg.to = initialTilt

  let hoverPart: PartId | null = null
  let focusedPart: PartId | null = null
  let dragPart: PartId | null = null
  let dragStartP: Vec2 | null = null
  let dragGrabM = 0
  let dragMoved = false

  // Focusable slider controls so Tab moves straight between the three interactive parts.
  stage.tabIndex = -1
  const sliderOrder: PartId[] = ["left-load", "fulcrum", "right-load"]
  const sliders = new Map<PartId, HTMLDivElement>()

  function syncSliders() {
    const d1 = round1(state.fulcrumM - state.leftM)
    const d2 = round1(state.rightM - state.fulcrumM)

    const leftEl = sliders.get("left-load")
    if (leftEl) {
      leftEl.setAttribute("aria-valuemin", String(-LEVER_BEAM_HALF_SPAN))
      leftEl.setAttribute("aria-valuemax", String(round1(state.fulcrumM - MIN_ARM_M)))
      leftEl.setAttribute("aria-valuenow", String(state.leftM))
      leftEl.setAttribute(
        "aria-valuetext",
        `Left load ${state.leftMass} kg, ${d1.toFixed(1)} m from fulcrum, torque ${state.physics.tau1.toFixed(0)} newton meters`,
      )
    }
    const fulcrumEl = sliders.get("fulcrum")
    if (fulcrumEl) {
      fulcrumEl.setAttribute("aria-valuemin", String(-FULCRUM_LIMIT_M))
      fulcrumEl.setAttribute("aria-valuemax", String(FULCRUM_LIMIT_M))
      fulcrumEl.setAttribute("aria-valuenow", String(state.fulcrumM))
      fulcrumEl.setAttribute(
        "aria-valuetext",
        `Fulcrum at ${state.fulcrumM.toFixed(1)} m, left arm ${d1.toFixed(1)} m, right arm ${d2.toFixed(1)} m`,
      )
    }
    const rightEl = sliders.get("right-load")
    if (rightEl) {
      rightEl.setAttribute("aria-valuemin", String(round1(state.fulcrumM + MIN_ARM_M)))
      rightEl.setAttribute("aria-valuemax", String(LEVER_BEAM_HALF_SPAN))
      rightEl.setAttribute("aria-valuenow", String(state.rightM))
      rightEl.setAttribute(
        "aria-valuetext",
        `Right load ${state.rightMass} kg, ${d2.toFixed(1)} m from fulcrum, torque ${state.physics.tau2.toFixed(0)} newton meters`,
      )
    }
  }

  function refreshPhysics() {
    state.physics = computePhysics(state)
    state.tiltDeg.to = targetTiltDegrees(state.physics, MAX_TILT_DEG)
    syncSliders()
    read.textContent = formatSummary(state)
  }

  function setInput(key: keyof Inputs, value: number) {
    if (value !== state[key]) L.change()
    state[key] = inputs[key].x = inputs[key].to = value
    inputs[key].v = 0
  }

  function moveFulcrum(nextM: number) {
    const clampedF = clamp(round1(nextM), -FULCRUM_LIMIT_M, FULCRUM_LIMIT_M)
    setInput("fulcrumM", clampedF)
    if (Math.max(state.leftM, inputs.leftM.to) > clampedF - MIN_ARM_M) {
      setInput("leftM", clamp(round1(clampedF - MIN_ARM_M), -LEVER_BEAM_HALF_SPAN, clampedF - MIN_ARM_M))
    }
    if (Math.min(state.rightM, inputs.rightM.to) < clampedF + MIN_ARM_M) {
      setInput("rightM", clamp(round1(clampedF + MIN_ARM_M), clampedF + MIN_ARM_M, LEVER_BEAM_HALF_SPAN))
    }
    refreshPhysics()
  }

  function moveLeftLoad(nextM: number) {
    setInput("leftM", clamp(round1(nextM), -LEVER_BEAM_HALF_SPAN, round1(state.fulcrumM - MIN_ARM_M)))
    refreshPhysics()
  }

  function moveRightLoad(nextM: number) {
    setInput("rightM", clamp(round1(nextM), round1(state.fulcrumM + MIN_ARM_M), LEVER_BEAM_HALF_SPAN))
    refreshPhysics()
  }

  function activatePart(part: PartId) {
    if (part === "left-load") {
      setInput("leftMass", nextMassPreset(state.leftMass))
    } else if (part === "right-load") {
      setInput("rightMass", nextMassPreset(state.rightMass))
    } else {
      moveFulcrum(0)
    }
    refreshPhysics()
    activated?.(part)
    L.wake()
  }

  function renderScene() {
    const out: Item[] = []
    const active = dragPart ?? focusedPart ?? hoverPart
    const fx = state.fulcrumM * UNIT
    const pivot: Vec3 = [fx, 0, PIVOT_Z]
    const tiltRad = deg(state.tiltDeg.x)
    const rot = (m: Mesh) => rotateY(m, tiltRad, pivot)
    const rotPt = (p: Vec3) => rotatePointY(p, tiltRad, pivot)

    // 1. Base rail & ruler labels along the track
    out.push({ mesh: box(-BASE_HALF_W, -9, 0, BASE_HALF_W, 9, 2.5), shade: true, inert: true })
    for (let m = -LEVER_BEAM_HALF_SPAN; m <= LEVER_BEAM_HALF_SPAN + 1e-6; m += LEVER_TICK_STEP) {
      const mx = round1(m) * UNIT
      const major = Math.abs(Math.round(m) - m) < 1e-6
      out.push({
        pts: [
          [mx, major ? 5.0 : 5.4, 2.55],
          [mx, 6.3, 2.55],
        ],
        cls: major ? "edge" : "lo",
        bias: 0.05,
      })
      if (major) {
        out.push(
          label(m === 0 ? "0" : `${m > 0 ? "+" : ""}${m}`, [mx, 8.1, 2.58], [1, 0, 0], [0, -1, 0], 1.85, {
            anchor: "middle",
            cls: "edge",
            bias: 0.06,
          }),
        )
      }
    }

    // 2. Fulcrum carriage + triangular prism + pivot axle
    const fulcrumCls = active === "fulcrum" ? "accent" : ""
    out.push({ mesh: box(fx - 4.2, -5.2, 2.5, fx + 4.2, 5.2, 4.5), shade: true, part: "fulcrum", cls: fulcrumCls })
    out.push({ mesh: fulcrumPrism(fx), shade: true, part: "fulcrum", cls: fulcrumCls })
    const axle = translate(rotateX(cylinder(0, 0, -5, 1.2, 10, 16), -Math.PI / 2), [fx, 0, PIVOT_Z])
    out.push({ mesh: axle, smooth: true, part: "fulcrum", cls: fulcrumCls, bias: 0.1 })

    // 3. Lever beam (rotates around pivot)
    const beam = rot(box(-BEAM_HALF_W, -4.5, PIVOT_Z, BEAM_HALF_W, 4.5, BEAM_TOP_Z))
    out.push({ mesh: beam, shade: true, inert: true })

    // 4. Ruler tick marks every 0.5 m along the beam (rotating with the beam)
    for (let m = -LEVER_BEAM_HALF_SPAN; m <= LEVER_BEAM_HALF_SPAN + 1e-6; m += LEVER_TICK_STEP) {
      const mx = round1(m) * UNIT
      const major = Math.abs(Math.round(m) - m) < 1e-6
      const topReach = major ? -1.5 : 1.4
      out.push({
        pts: [
          rotPt([mx, topReach, BEAM_TOP_Z + 0.08]),
          rotPt([mx, 4.54, BEAM_TOP_Z + 0.08]),
          rotPt([mx, 4.54, BEAM_TOP_Z - (major ? 1.4 : 0.8)]),
        ],
        cls: major ? "hi" : "edge",
        bias: 0.12,
      })
    }

    // 5. Two loads sitting on the beam
    const [lw, ld, lh] = loadDimensions(state.leftMass)
    const lx = state.leftM * UNIT
    const leftCls = active === "left-load" ? "accent" : state.physics.tilt === "left" ? "hi" : ""
    out.push({
      mesh: rot(box(lx - lw, -ld, BEAM_TOP_Z, lx + lw, ld, BEAM_TOP_Z + lh)),
      shade: true,
      part: "left-load",
      cls: leftCls,
      bias: 0.2,
    })

    const [rw, rd, rh] = loadDimensions(state.rightMass)
    const rx = state.rightM * UNIT
    const rightCls = active === "right-load" ? "accent" : state.physics.tilt === "right" ? "hi" : ""
    out.push({
      mesh: rot(box(rx - rw, -rd, BEAM_TOP_Z, rx + rw, rd, BEAM_TOP_Z + rh)),
      shade: true,
      part: "right-load",
      cls: rightCls,
      bias: 0.2,
    })

    // Mass labels lying on the top face of each load box
    const uTilted: Vec3 = [Math.cos(tiltRad), 0, -Math.sin(tiltRad)]
    const vFlat: Vec3 = [0, -1, 0]
    out.push(
      label(`${state.leftMass}kg`, rotPt([lx, 0.7, BEAM_TOP_Z + lh + 0.12]), uTilted, vFlat, 1.65, {
        anchor: "middle",
        part: "left-load",
        cls: active === "left-load" ? "accent" : "hi",
        bias: 0.25,
      }),
    )
    out.push(
      label(`${state.rightMass}kg`, rotPt([rx, 0.7, BEAM_TOP_Z + rh + 0.12]), uTilted, vFlat, 1.65, {
        anchor: "middle",
        part: "right-load",
        cls: active === "right-load" ? "accent" : "hi",
        bias: 0.25,
      }),
    )

    sc.render(cam, out)
  }

  const L = showcaseLoop(stage, (dt) => {
    let moving = false
    let changed = false
    for (const key of inputKeys) {
      const input = inputs[key]
      if (step(input, dt)) moving = true
      const next = key === "leftMass" || key === "rightMass" ? round1(input.x) : input.x
      if (state[key] !== next) {
        state[key] = next
        changed = true
      }
    }
    if (changed) refreshPhysics()
    if (step(state.tiltDeg, dt)) moving = true
    renderScene()
    return moving
  }, {
    defaults() {
      for (const key of inputKeys) inputs[key].to = defaults[key]
      if (state.g !== initialG) {
        state.g = initialG
        refreshPhysics()
      }
    },
    play(seconds) {
      const duration = 2.7
      const t = seconds + 1.5
      const phase = Math.floor(t / duration)
      const from = poses[Math.max(0, phase - 1) % poses.length]
      const to = poses[phase % poses.length]
      const eased = easeInOut((t % duration) / 0.95)
      let changed = false
      for (const key of inputKeys) {
        const target = from[key] + (to[key] - from[key]) * eased
        if (inputs[key].to !== target) {
          inputs[key].to = target
          changed = true
        }
      }
      return changed
    },
  })
  b.add(L.stop)

  for (const part of sliderOrder) {
    const ctrl = document.createElement("div")
    ctrl.className = "sr-only"
    ctrl.setAttribute("role", "slider")
    ctrl.setAttribute("tabindex", "0")
    ctrl.setAttribute("aria-label", PART_NAMES[part])
    ctrl.dataset.isoPart = part
    const onFocus = () => {
      focusedPart = part
      activated?.(part)
      L.wake()
    }
    const onBlur = () => {
      if (focusedPart === part) focusedPart = null
      L.wake()
    }
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === "ArrowLeft" || e.key === "ArrowDown") {
        e.preventDefault()
        if (part === "fulcrum") moveFulcrum(stepByTick(state.fulcrumM, -1, -FULCRUM_LIMIT_M, FULCRUM_LIMIT_M))
        else if (part === "left-load") moveLeftLoad(stepByTick(state.leftM, -1, -LEVER_BEAM_HALF_SPAN, round1(state.fulcrumM - MIN_ARM_M)))
        else moveRightLoad(stepByTick(state.rightM, -1, round1(state.fulcrumM + MIN_ARM_M), LEVER_BEAM_HALF_SPAN))
        activated?.(part)
        L.wake()
      } else if (e.key === "ArrowRight" || e.key === "ArrowUp") {
        e.preventDefault()
        if (part === "fulcrum") moveFulcrum(stepByTick(state.fulcrumM, 1, -FULCRUM_LIMIT_M, FULCRUM_LIMIT_M))
        else if (part === "left-load") moveLeftLoad(stepByTick(state.leftM, 1, -LEVER_BEAM_HALF_SPAN, round1(state.fulcrumM - MIN_ARM_M)))
        else moveRightLoad(stepByTick(state.rightM, 1, round1(state.fulcrumM + MIN_ARM_M), LEVER_BEAM_HALF_SPAN))
        activated?.(part)
        L.wake()
      } else if (e.key === "Enter" || e.key === " ") {
        e.preventDefault()
        activatePart(part)
      }
    }
    ctrl.addEventListener("focus", onFocus)
    ctrl.addEventListener("blur", onBlur)
    ctrl.addEventListener("keydown", onKeyDown)
    stage.appendChild(ctrl)
    sliders.set(part, ctrl)
    b.add(() => {
      ctrl.removeEventListener("focus", onFocus)
      ctrl.removeEventListener("blur", onBlur)
      ctrl.removeEventListener("keydown", onKeyDown)
      ctrl.remove()
    })
  }

  const dragHeightFor = (part: PartId) => (part === "fulcrum" ? 10 : BEAM_TOP_Z + 4)

  b.add(
    pointer(stage, {
      down: (p) => {
        const picked = sc.pick(p) as PartId | null
        if (picked && picked in PART_NAMES) {
          dragPart = picked
          dragStartP = p
          dragMoved = false
          dragGrabM = picked === "fulcrum" ? state.fulcrumM : picked === "left-load" ? state.leftM : state.rightM
          hoverPart = picked
          activated?.(picked)
          L.wake()
        }
      },
      move: (p) => {
        if (dragPart && dragStartP) {
          if (Math.hypot(p[0] - dragStartP[0], p[1] - dragStartP[1]) > 5) dragMoved = true
          const zPlane = dragHeightFor(dragPart)
          const wxNow = unproject(cam, p[0], p[1], zPlane)[0]
          const wxStart = unproject(cam, dragStartP[0], dragStartP[1], zPlane)[0]
          const deltaM = (wxNow - wxStart) / UNIT
          const nextM = round1(dragGrabM + deltaM)
          if (dragPart === "fulcrum") moveFulcrum(nextM)
          else if (dragPart === "left-load") moveLeftLoad(nextM)
          else moveRightLoad(nextM)
          L.wake()
          return
        }
        const picked = sc.pick(p) as PartId | null
        const nextHover = picked && picked in PART_NAMES ? picked : null
        if (nextHover !== hoverPart) {
          hoverPart = nextHover
          stage.style.cursor = hoverPart ? "grab" : ""
          L.wake()
        }
      },
      up: () => {
        if (dragPart && !dragMoved) {
          activatePart(dragPart)
        }
        dragPart = null
        dragStartP = null
        dragMoved = false
        stage.style.cursor = hoverPart ? "grab" : ""
        L.wake()
      },
      leave: () => {
        dragPart = null
        dragStartP = null
        dragMoved = false
        hoverPart = null
        stage.style.cursor = ""
        L.wake()
      },
    }),
  )

  b.add(() => svg.replaceChildren())
  refreshPhysics()

  let previousProps = props
  return {
    set: () => {},
    props: (next) => {
      let changed = false
      if (next.leftMass !== undefined && next.leftMass !== previousProps.leftMass) {
        setInput("leftMass", next.leftMass)
        changed = true
      }
      if (next.rightMass !== undefined && next.rightMass !== previousProps.rightMass) {
        setInput("rightMass", next.rightMass)
        changed = true
      }
      if (next.gravity !== undefined && next.gravity !== previousProps.gravity) {
        state.g = next.gravity
        L.change()
        changed = true
      }
      if (next.fulcrumPos !== undefined && next.fulcrumPos !== previousProps.fulcrumPos) {
        moveFulcrum(next.fulcrumPos)
        changed = false
      }
      if (next.leftPos !== undefined && next.leftPos !== previousProps.leftPos) {
        moveLeftLoad(next.leftPos)
        changed = false
      }
      if (next.rightPos !== undefined && next.rightPos !== previousProps.rightPos) {
        moveRightLoad(next.rightPos)
        changed = false
      }
      previousProps = next
      if (changed) refreshPhysics()
      L.wake()
    },
    debug: (on) => {
      sc.options.debug = on
      L.wake()
    },
    destroy: b.dispose,
  }
}

export const Lever = createFigure<LeverProps>("Lever", {
  id: "lever",
  label: "First-class lever on a fulcrum; drag the fulcrum or loads along the beam, or Tab and use Arrow keys to adjust positions and Enter to cycle mass.",
  rest: "L 20 kg @ 1.5 m (294 N·m) · R 10 kg @ 1.5 m (147 N·m) · Tips left",
  range: [0, 0.5, 1],
  focusable: true,
  defaults: {
    leftMass: 20,
    rightMass: 10,
    leftPos: -1.5,
    rightPos: 1.5,
    fulcrumPos: 0,
    gravity: DEFAULT_GRAVITY,
  },
  mount,
})
