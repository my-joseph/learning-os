import assert from "node:assert/strict";
import {
  boxesCollide,
  placePointLabel,
  pointToSegmentDistance,
  shouldSkipTickLabel,
} from "../src/lib/figureLayout";

// 1. Point label near x-axis (just below axis) nudges below tick labels instead of overlapping x-axis
const q02Placement = placePointLabel({
  sx: 87.3,
  sy: 148.3,
  label: "(-4, ?)",
  position: "top-right",
  axisX: 190,
  axisY: 130,
  showY: true,
  svgWidth: 380,
  svgHeight: 260,
  padding: 36,
});
assert.ok(
  q02Placement.y >= 130 + 18,
  `Point below x-axis should nudge below tick labels (>= 148), got y=${q02Placement.y}`
);

// 2. Point on or just above x-axis with "bottom-right" nudges above x-axis
const aboveXPlacement = placePointLabel({
  sx: 240,
  sy: 128,
  label: "(2, 0)",
  position: "bottom-right",
  axisX: 190,
  axisY: 130,
  showY: true,
  svgWidth: 380,
  svgHeight: 260,
  padding: 36,
});
assert.ok(
  aboveXPlacement.y + aboveXPlacement.height <= 130 - 4,
  `Point on/above x-axis should nudge above x-axis (<= 126), got bottom=${aboveXPlacement.y + aboveXPlacement.height}`
);

// 3. Point near y-axis tick zone nudges right or left clear of y-ticks
const nearYRight = placePointLabel({
  sx: 192,
  sy: 80,
  label: "(0, 3)",
  position: "top-left",
  axisX: 190,
  axisY: 130,
  showY: true,
  svgWidth: 380,
  svgHeight: 260,
  padding: 36,
});
assert.ok(
  nearYRight.x >= 190 + 6,
  `Point on/right of y-axis should nudge right of y-axis (>= 196), got x=${nearYRight.x}`
);

// 4. Tick label within 10px of a vertical dashed reference line is skipped
assert.equal(
  shouldSkipTickLabel({
    labelBox: { left: 276, top: 134, right: 288, bottom: 145 },
    dashedSegments: [{ x1: 282, y1: 36, x2: 282, y2: 224 }],
    pointLabelBoxes: [],
    axis: "x",
    tickCoord: 282,
  }),
  true
);

// Distant tick label is preserved
assert.equal(
  shouldSkipTickLabel({
    labelBox: { left: 100, top: 134, right: 112, bottom: 145 },
    dashedSegments: [{ x1: 282, y1: 36, x2: 282, y2: 224 }],
    pointLabelBoxes: [],
    axis: "x",
    tickCoord: 106,
  }),
  false
);

// 5. Tick label within 10px of a point label pill is skipped
assert.equal(
  shouldSkipTickLabel({
    labelBox: { left: 82, top: 134, right: 94, bottom: 145 },
    dashedSegments: [],
    pointLabelBoxes: [{ left: 95, top: 149, right: 155, bottom: 171 }],
    axis: "x",
    tickCoord: 88,
  }),
  true
);

// Geometry sanity checks
assert.equal(pointToSegmentDistance(10, 5, { x1: 0, y1: 0, x2: 10, y2: 0 }), 5);
assert.equal(
  boxesCollide(
    { left: 0, top: 0, right: 10, bottom: 10 },
    { left: 19, top: 0, right: 29, bottom: 10 },
    10
  ),
  true
);
assert.equal(
  boxesCollide(
    { left: 0, top: 0, right: 10, bottom: 10 },
    { left: 25, top: 0, right: 35, bottom: 10 },
    10
  ),
  false
);

console.log("figureLayout tests passed");
