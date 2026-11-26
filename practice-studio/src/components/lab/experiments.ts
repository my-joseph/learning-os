export const labExperiments = [
  { id: "lever", title: "Lever", caption: "Torque" },
  { id: "pulley", title: "Pulley", caption: "Force" },
  { id: "disk-method", title: "Disk method", caption: "Volume" },
  { id: "cube", title: "Cube", caption: "Isometric" },
  { id: "shapes", title: "Shapes", caption: "12 contours" },
  { id: "ui-components", title: "UI components", caption: "shadcn/ui" },
] as const;

export type LabExperiment = (typeof labExperiments)[number];
export type LabExperimentId = LabExperiment["id"];
