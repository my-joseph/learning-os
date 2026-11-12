export type FigureTheme = "indigo" | "blue" | "emerald" | "amber" | "rose" | "purple";

export interface Point2D {
  x: number;
  y: number;
}

// ----------------------------------------------------
// 2D GEOMETRY SPECIFICATION
// ----------------------------------------------------

export interface GeometryPolygonShape {
  type: "polygon";
  vertices: string[]; // references keys in points dict, e.g. ["A", "B", "C"]
  fill?: boolean;
  fillOpacity?: number;
  stroke?: string;
  strokeWidth?: number;
  strokeDasharray?: string;
}

export interface GeometrySegmentShape {
  type: "segment";
  from: string;
  to: string;
  stroke?: string;
  strokeWidth?: number;
  strokeDasharray?: string;
}

export interface GeometryCircleShape {
  type: "circle";
  center: string; // point key or "[x, y]"
  radius: number;
  fill?: boolean;
  fillOpacity?: number;
  stroke?: string;
  strokeWidth?: number;
  strokeDasharray?: string;
}

export interface GeometryArcShape {
  type: "arc";
  center: string;
  radius: number;
  startAngle: number; // degrees
  endAngle: number;   // degrees
  stroke?: string;
  strokeWidth?: number;
}

export interface GeometryEllipseShape {
  type: "ellipse";
  center: string;
  radiusX: number;
  radiusY: number;
  fill?: boolean;
  stroke?: string;
  strokeWidth?: number;
  strokeDasharray?: string;
}

export type GeometryShape =
  | GeometryPolygonShape
  | GeometrySegmentShape
  | GeometryCircleShape
  | GeometryArcShape
  | GeometryEllipseShape;

export interface GeometryRightAngleMarker {
  type: "right_angle";
  vertex: string; // The vertex where the 90 deg angle is
  arm1: string;   // Direction 1
  arm2: string;   // Direction 2
  size?: number;  // Visual square size in world units or px (default auto ~12% of min arm)
}

export interface GeometryAngleArcMarker {
  type: "angle_arc";
  vertex: string;
  arm1: string;
  arm2: string;
  label?: string; // LaTeX formatted, e.g. "45^\\circ"
  radius?: number;
}

export interface GeometryTickMarker {
  type: "tick";
  p1: string;
  p2: string;
  count?: number; // 1, 2, or 3 ticks
}

export type GeometryMarker =
  | GeometryRightAngleMarker
  | GeometryAngleArcMarker
  | GeometryTickMarker;

export interface GeometryPointLabel {
  type: "point";
  point: string;
  text?: string; // If omitted, uses point key name, e.g. "A"
  position?: "auto" | "top" | "bottom" | "left" | "right" | "top-left" | "top-right" | "bottom-left" | "bottom-right";
}

export interface GeometrySegmentLabel {
  type: "segment";
  p1: string;
  p2: string;
  text: string; // LaTeX formatted, e.g. "14\\text{ m}"
  side?: "auto" | "left" | "right" | "top" | "bottom" | "hypotenuse";
  offset?: number;
  highlight?: boolean;
}

export interface GeometryFreeLabel {
  type: "free";
  coord: [number, number];
  text: string;
}

export type GeometryLabel =
  | GeometryPointLabel
  | GeometrySegmentLabel
  | GeometryFreeLabel;

export interface Geometry2DSpec {
  kind: "geometry_2d";
  theme?: FigureTheme;
  title?: string;
  points: Record<string, [number, number]>;
  shapes: GeometryShape[];
  markers?: GeometryMarker[];
  labels?: GeometryLabel[];
}

// ----------------------------------------------------
// CARTESIAN GRAPH SPECIFICATION
// ----------------------------------------------------

export interface CartesianFunctionPlot {
  type: "function";
  fn?: string; // e.g. "2*x - 3" or "-x^2 + 4"
  coefficients?: number[]; // e.g. [2, -3] for 2x - 3 or [1, 0, -4] for x^2 - 4
  expression?: string; // LaTeX expression for legend/label, e.g. "y = 2x - 3"
  domain?: [number, number];
  color?: string; // semantic or hex
  strokeWidth?: number;
  strokeDasharray?: string;
}

export interface CartesianSegmentPlot {
  type: "segment";
  from: [number, number];
  to: [number, number];
  label?: string;
  color?: string;
  strokeWidth?: number;
  strokeDasharray?: string;
}

export interface CartesianPointPlot {
  type: "point";
  coord: [number, number];
  label?: string; // e.g. "(3, 4)"
  position?: "top" | "bottom" | "left" | "right" | "top-right" | "top-left" | "bottom-left" | "bottom-right";
  color?: string;
  hollow?: boolean;
}

export interface CartesianAreaPlot {
  type: "area";
  fn1: string;
  fn2?: string;
  domain: [number, number];
  color?: string;
  opacity?: number;
}

export interface CartesianSlopeTrianglePlot {
  type: "slope_triangle";
  p1: [number, number];
  p2: [number, number];
  showDeltas?: boolean;
}

export type CartesianPlot =
  | CartesianFunctionPlot
  | CartesianSegmentPlot
  | CartesianPointPlot
  | CartesianAreaPlot
  | CartesianSlopeTrianglePlot;

export interface CartesianGraphSpec {
  kind: "cartesian_graph";
  theme?: FigureTheme;
  title?: string;
  xRange: [number, number];
  yRange: [number, number];
  xStep?: number;
  yStep?: number;
  grid?: boolean;
  axes?: boolean;
  plots: CartesianPlot[];
}

// Unified Union Type
export type MathFigureSpec = Geometry2DSpec | CartesianGraphSpec;
