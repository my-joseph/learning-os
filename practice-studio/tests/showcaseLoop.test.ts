import assert from "node:assert/strict";
import test, { type TestContext } from "node:test";
import { createShowcaseController } from "../src/lib/isometric/showcase";

function fakeFrames(t: TestContext, keepEdits: boolean) {
  let restores = 0;
  let reduced = false;
  let visible = true;
  let running = false;
  const controller = createShowcaseController(keepEdits, () => { restores++; });
  t.mock.timers.enable({ apis: ["setInterval"] });
  const frame = setInterval(() => {
    if (visible) running = controller.tick(0.01, reduced);
  }, 10);
  t.after(() => clearInterval(frame));
  return {
    controller,
    advance(ms: number) { t.mock.timers.tick(ms); },
    reduce() { reduced = true; },
    setVisible(next: boolean) { visible = next; },
    restores: () => restores,
    running: () => running,
  };
}

test("engagement returns to defaults and release delays playback for two seconds", (t) => {
  const { controller, advance, restores } = fakeFrames(t, false);
  advance(500);
  assert.equal(controller.phase, "playing");
  assert.equal(controller.announce, false);

  controller.engage(true);
  assert.equal(controller.phase, "returning");
  assert.equal(restores(), 1);
  advance(400);
  assert.equal(controller.phase, "returning");
  assert.equal(controller.announce, false);
  advance(160);
  assert.equal(controller.phase, "engaged");
  assert.equal(controller.announce, true);

  controller.change();
  controller.engage(false);
  assert.equal(controller.phase, "waiting");
  assert.equal(controller.announce, false);
  assert.equal(restores(), 2);
  advance(1990);
  assert.equal(controller.phase, "waiting");
  advance(20);
  assert.equal(controller.phase, "playing");
  assert.ok(controller.playhead < 0.03);
});

test("a detail edit interrupts the return and holds through release and re-entry until Reset", (t) => {
  const { controller, advance, restores, running } = fakeFrames(t, true);
  controller.engage(true);
  advance(100);
  controller.change();
  assert.equal(controller.phase, "held");
  assert.equal(controller.announce, true);
  controller.engage(false);
  advance(10_000);
  assert.equal(controller.phase, "held");
  assert.equal(controller.announce, false);
  assert.equal(running(), false);
  controller.engage(true);
  assert.equal(controller.phase, "held");
  assert.equal(restores(), 1);

  controller.reset();
  assert.equal(controller.phase, "returning");
  assert.equal(restores(), 2);
  controller.engage(false);
  advance(2010);
  assert.equal(controller.phase, "playing");
});

test("reduced motion restores the demo and keeps interaction available without playback", (t) => {
  const { controller, advance, reduce, restores, running } = fakeFrames(t, true);
  advance(1000);
  reduce();
  advance(10);
  assert.equal(restores(), 1);
  assert.equal(controller.phase, "reduced");
  assert.equal(running(), false);

  controller.engage(true);
  controller.change();
  assert.equal(controller.announce, true);
  controller.engage(false);
  advance(10_000);
  assert.equal(controller.phase, "reduced");
  assert.equal(restores(), 1);
  controller.reset();
  assert.equal(restores(), 2);
});

test("dispatching no visible frames freezes both the script and the idle delay", (t) => {
  const { controller, advance, setVisible } = fakeFrames(t, false);
  advance(200);
  const playhead = controller.playhead;
  setVisible(false);
  advance(10_000);
  assert.equal(controller.playhead, playhead);

  controller.engage(true);
  controller.engage(false);
  advance(5000);
  assert.equal(controller.phase, "waiting");
  setVisible(true);
  advance(2010);
  assert.equal(controller.phase, "playing");
});
