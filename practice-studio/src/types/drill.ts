export type VisualElementType =
  | "polygon"
  | "circle"
  | "line"
  | "dimension-label"
  | "angle-arc"
  | "cylinder"
  | "box-3d"
  | "cone"
  | "point"
  | "axis"
  | "grid"
  | "text";

export interface VisualElement {
  type: VisualElementType;
  points?: [number, number][];
  center?: [number, number];
  coord?: [number, number];
  radius?: number;
  radiusX?: number;
  radiusY?: number;
  height?: number;
  width?: number;
  depth?: number;
  stroke?: string;
  fill?: string;
  strokeWidth?: number;
  strokeDasharray?: string;
  rightAngleAt?: [number, number];
  start?: [number, number];
  end?: [number, number];
  label?: string;
  position?: "top" | "bottom" | "left" | "right" | "center" | "hypotenuse";
  offset?: number;
  highlight?: boolean;
  startAngle?: number;
  endAngle?: number;
  x?: number;
  y?: number;
  fontSize?: number;
  color?: string;
}

/**
 * Universal Interactive Capability Spec
 * Supports Geometry, Vectors, Function Slopes, and Kinematics
 */
export interface InteractiveSpec {
  mode: "pythagoras-drag" | "cylinder-slider" | "trapezoid-drag" | "circle-radius-drag" | "vector-scrub" | "slope-probe";
  initialParams: Record<string, number>;
  constraints?: {
    min?: number;
    max?: number;
    step?: number;
  };
  labels?: {
    x?: string;
    y?: string;
    result?: string;
  };
}

export interface VisualSpec {
  type: "geometry-2d" | "geometry-3d-wireframe" | "coordinate-plane" | "physics-diagram";
  viewBox: { width: number; height: number };
  elements: VisualElement[];
  interactive?: InteractiveSpec; // Interactive Playground Specification
}

export interface Step {
  latex: string;
  explain: string;
}

export interface ChoiceOption {
  id: string;
  label: string;
  trapTag?: string;
  tag?: string;
}

export interface AnswerSpec {
  type:
    | "number"
    | "complex"
    | "expression"
    | "solution_set"
    | "tuple"
    | "vector"
    | "choice"
    | "text"
    | "code_output"
    | "predict_output"
    | "line_number"
    | "find_bug";
  value?: string;
  forms?: string[];
  variables?: string[];
  values?: string[];
  components?: (number | string)[];
  dimension?: number;
  vectorNotation?: boolean;
  labels?: string[];
  acceptComplex?: boolean;
  options?: ChoiceOption[];
  correct?: string;
  accepted?: string[];
  tokens?: string[];
  correctLine?: number;
  flawExplanation?: string;
  commonTrapTag?: string;
  trapValue?: string;
  flawTag?: string;
}

export interface ReferenceBadge {
  code: string;
  title: string;
  notionUrl: string | null;
}

export interface CheckComponent {
  label: string;
  ok: boolean;
}

export interface CheckDiagnostic {
  code: string;
  message: string;
}

export interface CheckResult {
  verdict: "correct" | "equivalent_not_in_form" | "partial" | "incorrect" | "parse_error" | "invalid input" | "skipped";
  message: string;
  components: CheckComponent[];
  diagnostics: CheckDiagnostic[];
  trapMatched?: boolean;
}

export interface TestCase {
  id: string;
  name: string;
  testCode: string;
  isHidden?: boolean;
}

export interface TestResult {
  name: string;
  passed: boolean;
  durationMs?: number;
  error?: string;
  expected?: string;
  actual?: string;
}

export interface TestRunReport {
  allPassed: boolean;
  score: number;
  passedCount: number;
  totalCount: number;
  visibleResults: TestResult[];
  hiddenPassed: number;
  hiddenTotal: number;
  executionTimeMs: number;
  rawOutput?: string;
}

export interface AttemptRecord {
  input: string;
  ts: string;
  verdict: string;
  diagnosticCodes?: string[];
  matchedTrap?: string;
}

export interface ProblemState {
  userInput: string;
  score: number | null;
  divergedStep: number | null;
  mistakes: string[];
  mistakeNote?: string;
  skipped?: boolean;
  lastCheck?: CheckResult | null;
  lastTestReport?: TestRunReport | null;
  userCode?: string;
  attempts?: AttemptRecord[];
  hintsRevealed?: number;
  durationMs?: number;
}

export type EngineeringArchetype =
  | "problem-solving"
  | "debugging"
  | "code-tracing"
  | "refactoring"
  | "project-based";

export type EngineeringCompetency =
  | "data-handling"
  | "state-management"
  | "component-design"
  | "api-integration"
  | "typescript"
  | "architecture"
  | "performance";

export interface Problem {
  id: string;
  templateKey: string;
  level: number;
  levelLabel: string;
  category: string;
  context?: string;
  prompt: string;
  display?: string;
  plainText?: string;
  codeSnippet?: string;
  language?: string;
  codeType?:
    | "problem-solving"
    | "debugging"
    | "code-tracing"
    | "refactoring"
    | "project-based"
    | "kata"
    | "implement"
    | "refactor"
    | "find-bug"
    | "predict-output"
    | string;
  archetype?: EngineeringArchetype;
  competencies?: EngineeringCompetency[];
  starterCode?: string;
  solutionCode?: string;
  entryPoint?: string;
  visibleTests?: TestCase[];
  hiddenTests?: TestCase[];
  workspaceFile?: string;
  workspaceDir?: string;
  cursorUrl?: string;
  vscodeUrl?: string;
  cursorFolderUrl?: string;
  vscodeFolderUrl?: string;
  visual?: VisualSpec;
  answerSpec: AnswerSpec;
  answerDisplay: string;
  answerPlain: string;
  inputHint?: string;
  checkpointHint: string;
  commonTrapTag?: string;
  trapValue?: string;
  flawTag?: string;
  form?: string;
  skill?: string;
  verificationLevel?: "machine-verified" | "partial" | "human-reviewed";
  fingerprint?: string;
  qualityGates?: Record<string, unknown>;
  steps: Step[];
  references?: string[];
  referenceBadges?: ReferenceBadge[];
  state: ProblemState;
}

export interface MistakeTag {
  id: string;
  label: string;
  name: string;
  autoFrom: string[];
}

export interface DrillConfig {
  questionCount: number;
  difficulty: string;
  difficultyMode: string;
}

export interface SessionSummary {
  practiceStatus: "Ready" | "In Progress" | "Graded" | "Needs Retry";
  score: number;
  maxScore: number;
  accuracyPct: number;
  skippedCount?: number;
  skippedProblems?: string[];
  mistakeCategories: string[];
  divergedStepsSummary: string;
  attemptDate: string | null;
  syncedToNotionAt?: string | null;
  notionPageId?: string | null;
}

export interface DrillDocument {
  schemaVersion: string;
  drillId: string;
  subject: "MATH" | "PRG";
  unitCode: string;
  unitTitle: string;
  chapterCode: string;
  topicCode: string;
  unitNotionUrl: string | null;
  createdAt: string;
  config: DrillConfig;
  mistakeTags: MistakeTag[];
  problems: Problem[];
  sessionSummary: SessionSummary;
  localFilePath: string;
}

export interface DrillListItem {
  drillId: string;
  subject?: "MATH" | "PRG";
  unitCode: string;
  unitTitle: string;
  createdAt: string;
  questionCount: number;
  difficultyMode: string;
  practiceStatus?: "Ready" | "In Progress" | "Graded" | "Needs Retry";
  score?: number;
  maxScore?: number;
  answeredCount?: number;
  localFilePath: string;
}
