import type {
  DrillDocument,
  Problem,
  ProblemState,
  SessionSummary,
  TestCase,
} from "@/types/drill";
import { deriveReviewStatus, type ReviewStatus } from "@/lib/codeStatus";

export const ALWAYS_STRIPPED_LAB_FIELDS = [
  "blindSolve",
  "review",
  "trapMutant",
  "trapMutants",
  "mutants",
  "hiddenTests",
  "solutionCode",
  "verify",
  "qualityGates",
  "targetsWeakSpots",
  "_reference",
  "referenceDir",
] as const;

export const ALWAYS_STRIPPED_MILESTONE_FIELDS = [
  "trapMutant",
  "trapMutants",
  "mutants",
  "hiddenTests",
  "blindSolve",
  "solutionCode",
  "verify",
  "qualityGates",
  "qualityChecks",
] as const;

export interface LabMilestoneDetail {
  id: string;
  title: string;
  goal: string;
  description: string;
  units: string[];
  points?: number;
  visibleTestFiles: string[];
  visibleTests: TestCase[];
  testCommand: string;
  checkCommand: string;
  mainFile: string | null;
  vscodeFolderUrl: string;
  cursorFolderUrl: string;
  vscodeUrl: string | null;
  cursorUrl: string | null;
  reviewStatus: ReviewStatus;
  state: ProblemState;
}

export interface LabProgressSummary {
  passedCount: number;
  reviseCount: number;
  notStartedCount: number;
  totalCount: number;
  practiceStatus: "Ready" | "In Progress" | "Graded" | "Needs Retry";
  score: number;
  maxScore: number;
  updatedAt: string | null;
  milestones: Record<string, ReviewStatus>;
}

export interface LabListItem {
  id: string;
  labId: string;
  title: string;
  unitCode: string;
  chapterCode: string;
  chapterTitle?: string;
  topicCode: string;
  topicTitle?: string;
  unitsUsed: string[];
  kind: string;
  level?: number;
  milestoneCount: number;
  practiceStatus: "Ready" | "In Progress" | "Graded" | "Needs Retry";
  passedCount: number;
  reviseCount: number;
  score: number;
  maxScore: number;
  progress: LabProgressSummary;
}

export interface LabDetailResponse {
  id: string;
  labId: string;
  title: string;
  unitCode: string;
  chapterCode: string;
  topicCode: string;
  unitsUsed: string[];
  kind: string;
  level: number;
  domain: string;
  scenario: string;
  readme: string;
  workspaceDir: string;
  vscodeFolderUrl: string;
  cursorFolderUrl: string;
  testCommand: string;
  checkCommand: string;
  unitNotionUrl: string | null;
  milestones: LabMilestoneDetail[];
  progress: LabProgressSummary;
  sessionSummary: SessionSummary;
}

export const FORBIDDEN_LAB_LINE_RE =
  /(?:_reference|test:reference|check:reference|check:hidden|\btrapMutants?\b|\bhiddenTests\b|\bsolutionCode\b)/i;

/**
 * Strip any README lines referencing `_reference`, `test:reference`, `check:reference`,
 * `check:hidden`, `trapMutant`, or `solutionCode`.
 */
export function sanitizeLabReadme(rawReadme: string): string {
  if (!rawReadme) return "";
  return rawReadme
    .split(/\r?\n/)
    .filter((line) => !FORBIDDEN_LAB_LINE_RE.test(line))
    .join("\n")
    .trim();
}

/**
 * Parse `### M1 — ...` milestone sections from a lab README.
 */
export function parseReadmeMilestones(readme: string): Record<string, string> {
  const result: Record<string, string> = {};
  if (!readme) return result;

  const lines = readme.split(/\r?\n/);
  let currentId: string | null = null;
  let buffer: string[] = [];

  const flush = () => {
    if (currentId) {
      const cleaned = buffer
        .filter((ln) => !/^Run this milestone's visible checks/i.test(ln.trim()))
        .join("\n")
        .trim();
      if (cleaned) {
        result[currentId.toUpperCase()] = cleaned;
      }
    }
    currentId = null;
    buffer = [];
  };

  for (const line of lines) {
    const h2Match = /^##\s+/.exec(line);
    if (h2Match && !/^###/.test(line)) {
      flush();
      continue;
    }
    const msMatch = /^###\s+(M\d+)\b/i.exec(line);
    if (msMatch) {
      flush();
      currentId = msMatch[1].toUpperCase();
      continue;
    }
    if (currentId) {
      buffer.push(line);
    }
  }
  flush();
  return result;
}

export function makeDefaultMilestoneState(
  rawState?: Record<string, unknown> | null
): ProblemState {
  const s = (rawState && typeof rawState === "object" ? rawState : {}) as Partial<ProblemState>;
  return {
    userInput: typeof s.userInput === "string" ? s.userInput : "",
    userCode: typeof s.userCode === "string" ? s.userCode : "",
    score: typeof s.score === "number" ? s.score : null,
    divergedStep: typeof s.divergedStep === "number" ? s.divergedStep : null,
    mistakes: Array.isArray(s.mistakes) ? s.mistakes : [],
    mistakeNote: typeof s.mistakeNote === "string" ? s.mistakeNote : "",
    skipped: Boolean(s.skipped),
    lastCheck: s.lastCheck ?? null,
    lastTestReport: s.lastTestReport ?? null,
    attempts: Array.isArray(s.attempts) ? s.attempts : [],
    reviews: Array.isArray(s.reviews) ? s.reviews : [],
    hintsRevealed: typeof s.hintsRevealed === "number" ? s.hintsRevealed : 0,
    setupRevealedBeforeAnswer: Boolean(s.setupRevealedBeforeAnswer),
    solutionRevealedBeforeAnswer: Boolean(s.solutionRevealedBeforeAnswer),
    durationMs: typeof s.durationMs === "number" ? s.durationMs : 0,
  };
}

export function lookupStateForMilestone(
  problemsMap: Record<string, unknown> | undefined,
  milestoneId: string
): Record<string, unknown> | null {
  if (!problemsMap || typeof problemsMap !== "object") return null;
  if (milestoneId in problemsMap) {
    return problemsMap[milestoneId] as Record<string, unknown>;
  }
  const upper = milestoneId.toUpperCase();
  for (const [k, v] of Object.entries(problemsMap)) {
    if (k.toUpperCase() === upper && v && typeof v === "object") {
      return v as Record<string, unknown>;
    }
  }
  return null;
}

/**
 * Compute progress summary for a lab from its milestone definitions and progress object.
 */
export function summarizeLabProgress(
  milestones: readonly { id?: string }[],
  progress: {
    updatedAt?: string;
    sessionSummary?: Record<string, unknown>;
    problems?: Record<string, unknown>;
  } | null
): LabProgressSummary {
  const totalCount = milestones.length;
  const problemsMap = progress?.problems;
  const milestoneStatuses: Record<string, ReviewStatus> = {};
  let passedCount = 0;
  let reviseCount = 0;
  let hasAnyActivity = false;

  for (const ms of milestones) {
    const mid = String(ms.id || "").trim();
    if (!mid) continue;
    const rawState = lookupStateForMilestone(problemsMap, mid);
    const state = makeDefaultMilestoneState(rawState);
    const reviewStatus = deriveReviewStatus(state.reviews);
    milestoneStatuses[mid] = reviewStatus;
    if (reviewStatus === "pass") {
      passedCount += 1;
      hasAnyActivity = true;
    } else if (reviewStatus === "revise") {
      reviseCount += 1;
      hasAnyActivity = true;
    } else if (
      state.lastTestReport ||
      state.score !== null ||
      (state.mistakes && state.mistakes.length > 0) ||
      Boolean(state.mistakeNote && state.mistakeNote.trim())
    ) {
      hasAnyActivity = true;
    }
  }

  const notStartedCount = Math.max(0, totalCount - passedCount - reviseCount);
  const rawSummary = (progress?.sessionSummary || {}) as Partial<SessionSummary>;

  let practiceStatus: "Ready" | "In Progress" | "Graded" | "Needs Retry" = "Ready";
  if (totalCount > 0 && passedCount === totalCount) {
    practiceStatus = "Graded";
  } else if (rawSummary.practiceStatus === "Needs Retry" && reviseCount > 0) {
    practiceStatus = "Needs Retry";
  } else if (hasAnyActivity || passedCount > 0 || reviseCount > 0) {
    practiceStatus = "In Progress";
  } else if (
    rawSummary.practiceStatus === "In Progress" ||
    rawSummary.practiceStatus === "Graded" ||
    rawSummary.practiceStatus === "Needs Retry"
  ) {
    practiceStatus = rawSummary.practiceStatus;
  }

  return {
    passedCount,
    reviseCount,
    notStartedCount,
    totalCount,
    practiceStatus,
    score: passedCount,
    maxScore: totalCount,
    updatedAt: typeof progress?.updatedAt === "string" ? progress.updatedAt : null,
    milestones: milestoneStatuses,
  };
}

/**
 * Adapt a `LabDetailResponse` into a `DrillDocument` so `StudioClient`, `StudioShell`,
 * `QuizPaginationBar`, and `CodeDashboard` can render labs without duplicating components.
 */
export function labToDrillDocument(lab: LabDetailResponse): DrillDocument {
  const problems: Problem[] = lab.milestones.map((ms) => {
    const genericReadmeBoilerplate =
      /^Complete the milestone requirements in the starter project\.?$/i.test(
        ms.description.trim()
      );
    let promptText = ms.description || ms.goal;
    if (genericReadmeBoilerplate) {
      promptText =
        ms.goal && !genericReadmeBoilerplate
          ? ms.goal
          : lab.scenario
          ? `${lab.scenario}\n\nMilestone focus: **${ms.title}**.`
          : ms.title;
    }

    return {
      id: ms.id,
      templateKey: lab.id,
      level: lab.level || 3,
      levelLabel: `Level ${lab.level || 3}`,
      category: ms.title,
      entryPoint: ms.title,
      prompt: promptText,
      codeType: "project-based",
      archetype: "project-based",
      visibleTests: ms.visibleTests,
      visibleTestFiles: ms.visibleTestFiles,
      testCommand: ms.testCommand,
      checkCommand: ms.checkCommand,
      mainFile: ms.mainFile,
      workspaceDir: lab.workspaceDir,
      workspaceFile: ms.mainFile
        ? `${lab.workspaceDir}/${ms.mainFile}`
        : `${lab.workspaceDir}/src`,
      vscodeFolderUrl: ms.vscodeFolderUrl || lab.vscodeFolderUrl,
      cursorFolderUrl: ms.cursorFolderUrl || lab.cursorFolderUrl,
      ...(ms.vscodeUrl ? { vscodeUrl: ms.vscodeUrl } : {}),
      ...(ms.cursorUrl ? { cursorUrl: ms.cursorUrl } : {}),
      answerSpec: { type: "code_output" },
      checkpointHint: "",
      state: ms.state,
    };
  });

  return {
    schemaVersion: "2.0",
    drillId: lab.id,
    subject: "PRG",
    unitCode: lab.unitCode || lab.chapterCode,
    unitTitle: lab.title,
    chapterCode: lab.chapterCode,
    topicCode: lab.topicCode,
    unitNotionUrl: lab.unitNotionUrl,
    createdAt: "",
    config: {
      questionCount: lab.milestones.length,
      difficulty: `Level ${lab.level}`,
      difficultyMode: "Project Lab",
    },
    mistakeTags: [],
    problems,
    sessionSummary: lab.sessionSummary,
    localFilePath: lab.workspaceDir,
    labReadme: lab.readme,
  };
}
