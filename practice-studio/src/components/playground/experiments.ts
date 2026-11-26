export const playgroundExperiments = [
  { id: "lever", title: "Lever", caption: "Torque" },
  { id: "pulley", title: "Pulley", caption: "Force" },
  { id: "collisions", title: "Collisions", caption: "Momentum" },
  { id: "disk-method", title: "Disk method", caption: "Volume" },
  { id: "cube", title: "Cube", caption: "Isometric" },
  { id: "shapes", title: "Shapes", caption: "12 contours" },
  { id: "ui-components", title: "UI components", caption: "shadcn/ui" },
] as const;

export type PlaygroundExperiment = (typeof playgroundExperiments)[number];
export type PlaygroundExperimentId = PlaygroundExperiment["id"];
