import { reducedMotion } from "./motion"
import { createShowcaseController, type ShowcaseScript } from "./showcase"
import { bag, loop, type Loop, type Tick } from "./stage"

type ShowcaseLoop = Loop & { change(): void; returning(): boolean }
const resets = new WeakMap<HTMLElement, () => void>()

export function resetShowcase(button: HTMLElement) {
  const boundary = button.closest<HTMLElement>("[data-showcase]")
  if (boundary) resets.get(boundary)?.()
}

/** Runs a figure's script on its existing stage tick and uses the whole card as its input boundary. */
export function showcaseLoop(stage: HTMLElement, tick: Tick, script?: ShowcaseScript): ShowcaseLoop {
  const boundary = stage.closest<HTMLElement>("[data-showcase]")
  if (!boundary || !script) return { ...loop(stage, tick), change() {}, returning: () => false }

  const b = bag()
  const live = stage.querySelector("[data-iso-live]")
  let dirty = true
  let moving = false
  const controller = createShowcaseController(boundary.dataset.showcase === "detail", () => {
    script.defaults()
    dirty = true
  })
  const updateLive = () => {
    const value = controller.announce ? "polite" : "off"
    if (live?.getAttribute("aria-live") !== value) live?.setAttribute("aria-live", value)
  }

  let hovered = matchMedia("(any-hover: hover)").matches && boundary.matches(":hover")
  let focused = boundary.contains(document.activeElement)
  const pointers = new Set<number>()
  const update = () => controller.engage(hovered || focused || pointers.size > 0)

  update()
  const shared = loop(stage, (dt, now) => {
    const running = controller.tick(dt, reducedMotion())
    updateLive()
    if (controller.phase === "playing" && script.play(controller.playhead)) dirty = true
    if (dirty || moving) {
      dirty = false
      moving = !!tick(dt, now)
    }
    return running || moving
  })
  b.add(shared.stop)

  const input = () => {
    update()
    updateLive()
    shared.wake()
  }
  const enter = (event: PointerEvent) => {
    if (event.pointerType === "touch") return
    hovered = true
    input()
  }
  const leave = (event: PointerEvent) => {
    if (event.pointerType === "touch") return
    hovered = false
    input()
  }
  const press = (event: PointerEvent) => {
    pointers.add(event.pointerId)
    // A touch on the SVG engages for the contact. Keep native controls focusable.
    if (event.pointerType === "touch" && event.target instanceof Element &&
        stage.contains(event.target) && !event.target.closest("a, button, input, textarea, select, [contenteditable]")) {
      event.preventDefault()
    }
    input()
  }
  const release = (event: PointerEvent) => {
    if (!pointers.delete(event.pointerId)) return
    if (event.pointerType === "mouse") {
      hovered = boundary.contains(document.elementFromPoint(event.clientX, event.clientY))
    }
    input()
  }
  const focus = () => {
    focused = true
    input()
  }
  const blur = (event: FocusEvent) => {
    focused = event.relatedTarget instanceof Node && boundary.contains(event.relatedTarget)
    input()
  }
  const reset = () => {
    controller.reset()
    updateLive()
    shared.wake()
  }

  resets.set(boundary, reset)
  boundary.addEventListener("pointerenter", enter)
  boundary.addEventListener("pointerleave", leave)
  boundary.addEventListener("pointerdown", press, true)
  boundary.addEventListener("focusin", focus)
  boundary.addEventListener("focusout", blur)
  // Let the figure finish the drag before deciding whether to retain its values.
  window.addEventListener("pointerup", release)
  window.addEventListener("pointercancel", release)
  b.add(() => {
    resets.delete(boundary)
    boundary.removeEventListener("pointerenter", enter)
    boundary.removeEventListener("pointerleave", leave)
    boundary.removeEventListener("pointerdown", press, true)
    boundary.removeEventListener("focusin", focus)
    boundary.removeEventListener("focusout", blur)
    window.removeEventListener("pointerup", release)
    window.removeEventListener("pointercancel", release)
  })
  return {
    wake() {
      dirty = true
      shared.wake()
    },
    change() {
      controller.change()
      updateLive()
      shared.wake()
    },
    returning: () => controller.phase === "returning",
    stop: b.dispose,
  }
}
