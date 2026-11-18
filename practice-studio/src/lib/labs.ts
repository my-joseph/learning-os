import fs from "fs";
import path from "path";
import type { SessionSummary, TestCase } from "@/types/drill";
import { deriveReviewStatus } from "@/lib/codeStatus";
import { getLabsDir, getWorkspaceRoot, isSafeId, loadIdMapTitles } from "@/lib/paths";
import { cleanCurriculumTitle } from "@/lib/drillGrouping";
import { readProgress } from "@/lib/progress";
import { isLabId } from "@/lib/routes";
import {
  ALWAYS_STRIPPED_LAB_FIELDS,
  ALWAYS_STRIPPED_MILESTONE_FIELDS,
  FORBIDDEN_LAB_LINE_RE,
  labToDrillDocument,
  lookupStateForMilestone,
  makeDefaultMilestoneState,
  parseReadmeMilestones,
  sanitizeLabReadme,
  summarizeLabProgress,
  type LabDetailResponse,
  type LabListItem,
  type LabMilestoneDetail,
  type LabProgressSummary,
} from "@/lib/labModel";

export {
  ALWAYS_STRIPPED_LAB_FIELDS,
  ALWAYS_STRIPPED_MILESTONE_FIELDS,
  labToDrillDocument,
  parseReadmeMilestones,
  sanitizeLabReadme,
  summarizeLabProgress,
  type LabDetailResponse,
  type LabListItem,
  type LabMilestoneDetail,
  type LabProgressSummary,
};

const TEST_TITLE_RE =
  /\b(?:test|it)\s*\(\s*(?:"((?:\\.|[^"\\])*)"|'((?:\\.|[^'\\])*)'|`((?:\\.|[^`\\])*)`)/g;

function globToRegExp(globPattern: string): RegExp {
  const normalized = globPattern.replace(/\\/g, "/").replace(/^tests\//, "");
  const escaped = normalized
    .replace(/[.+^${}()|[\]\\]/g, "\\$&")
    .replace(/\*/g, ".*")
    .replace(/\?/g, ".");
  return new RegExp(`^${escaped}$`, "i");
}

function resolveMilestoneVisibleTestFiles(
  labDir: string,
  ms: Record<string, unknown>
): string[] {
  const testsDir = path.join(labDir, "tests");
  if (!fs.existsSync(testsDir) || !fs.statSync(testsDir).isDirectory()) {
    return [];
  }

  const entries = fs
    .readdirSync(testsDir, { withFileTypes: true })
    .filter(
      (e) =>
        e.isFile() &&
        /\.test\.(?:ts|tsx|js|jsx)$/i.test(e.name) &&
        !e.name.toLowerCase().includes("hidden") &&
        !e.name.endsWith(".test-d.ts")
    )
    .map((e) => e.name)
    .sort();

  const visPattern = typeof ms.visibleTests === "string" ? ms.visibleTests.trim() : "";
  const testPattern = typeof ms.testPattern === "string" ? ms.testPattern.trim() : "";
  const mid = typeof ms.id === "string" ? ms.id.trim().toLowerCase() : "";

  let matched: string[] = [];
  if (visPattern && !FORBIDDEN_LAB_LINE_RE.test(visPattern)) {
    const re = globToRegExp(visPattern);
    matched = entries.filter((name) => re.test(name));
  } else if (testPattern && !FORBIDDEN_LAB_LINE_RE.test(testPattern)) {
    const lowerPat = testPattern.toLowerCase();
    matched = entries.filter((name) => name.toLowerCase().includes(lowerPat));
  } else if (mid) {
    matched = entries.filter((name) => name.toLowerCase().startsWith(`${mid}_`));
  }

  return matched.map((name) => `tests/${name}`);
}

function extractVisibleTestCases(
  labDir: string,
  milestoneId: string,
  relTestFiles: readonly string[]
): TestCase[] {
  const cases: TestCase[] = [];
  for (const relFile of relTestFiles) {
    if (FORBIDDEN_LAB_LINE_RE.test(relFile)) continue;
    const absFile = path.resolve(labDir, relFile);
    const relCheck = path.relative(labDir, absFile);
    if (relCheck.startsWith("..") || path.isAbsolute(relCheck)) continue;
    if (!fs.existsSync(absFile)) continue;

    try {
      const content = fs.readFileSync(absFile, "utf-8");
      const titles: string[] = [];
      let match: RegExpExecArray | null;
      TEST_TITLE_RE.lastIndex = 0;
      while ((match = TEST_TITLE_RE.exec(content)) !== null) {
        const title = (match[1] || match[2] || match[3] || "").trim();
        if (title && !FORBIDDEN_LAB_LINE_RE.test(title)) {
          titles.push(title);
        }
      }
      const filteredTitles =
        titles.length > 1 && /^Milestone\s+\d+\s*:/i.test(titles[0])
          ? titles.slice(1)
          : titles;

      for (const title of filteredTitles) {
        cases.push({
          id: `${milestoneId}-T${cases.length + 1}`,
          name: title,
          testCode: "",
        });
      }
    } catch {
      // Ignore unreadable test file
    }
  }

  if (cases.length === 0 && relTestFiles.length > 0) {
    for (const relFile of relTestFiles) {
      cases.push({
        id: `${milestoneId}-F${cases.length + 1}`,
        name: relFile,
        testCode: "",
      });
    }
  }
  return cases;
}

function resolveMilestoneMainFile(
  labDir: string,
  ms: Record<string, unknown>
): { mainFile: string | null; vscodeUrl: string | null; cursorUrl: string | null } {
  const rawMain =
    ms.mainFile ?? ms.file ?? ms.sourceFile ?? ms.entryFile ?? null;
  if (typeof rawMain !== "string" || !rawMain.trim()) {
    return { mainFile: null, vscodeUrl: null, cursorUrl: null };
  }
  const candidate = rawMain.trim().replace(/^\/+/, "");
  if (FORBIDDEN_LAB_LINE_RE.test(candidate)) {
    return { mainFile: null, vscodeUrl: null, cursorUrl: null };
  }
  const absTarget = path.resolve(labDir, candidate);
  const relToLab = path.relative(labDir, absTarget);
  if (
    !relToLab ||
    relToLab.startsWith("..") ||
    path.isAbsolute(relToLab) ||
    relToLab.split(/[\\/]+/).includes("_reference") ||
    relToLab.split(/[\\/]+/).includes(".canonical")
  ) {
    return { mainFile: null, vscodeUrl: null, cursorUrl: null };
  }
  const cleanRel = relToLab.replace(/\\/g, "/");
  const absNormalized = absTarget.startsWith("/") ? absTarget : `/${absTarget}`;
  return {
    mainFile: cleanRel,
    vscodeUrl: `vscode://file${absNormalized}`,
    cursorUrl: `cursor://file${absNormalized}`,
  };
}

function resolveNotionUrlForLab(
  labId: string,
  unitCode: string,
  chapterCode: string
): string | null {
  try {
    const idMapPath = path.join(getWorkspaceRoot(), "id_map.json");
    if (!fs.existsSync(idMapPath)) return null;
    const idMap = JSON.parse(fs.readFileSync(idMapPath, "utf-8")) as Record<
      string,
      string | { id?: string }
    >;
    for (const key of [labId, unitCode, chapterCode]) {
      if (!key) continue;
      const entry = idMap[key];
      const rawId = typeof entry === "string" ? entry : entry?.id;
      if (typeof rawId === "string" && rawId.trim()) {
        return `https://notion.so/${rawId.replace(/-/g, "")}`;
      }
    }
  } catch {
    // Ignore id_map read errors
  }
  return null;
}

/**
 * List all project labs in `getLabsDir()` with milestone counts and progress summaries.
 * Never reads or returns anything under `labs/_reference/`.
 */
export function listLabsFromDisk(labsDir: string = getLabsDir()): LabListItem[] {
  if (!fs.existsSync(labsDir)) return [];

  const idMapTitles = loadIdMapTitles();
  const entries = fs.readdirSync(labsDir, { withFileTypes: true });
  const items: LabListItem[] = [];

  for (const entry of entries) {
    if (!entry.isDirectory()) continue;
    if (entry.name.startsWith("_") || entry.name.startsWith(".")) continue;
    if (!isLabId(entry.name) || !isSafeId(entry.name)) continue;

    const labDir = path.join(labsDir, entry.name);
    const configPath = path.join(labDir, "lab.config.json");
    if (!fs.existsSync(configPath)) continue;

    try {
      const raw = JSON.parse(fs.readFileSync(configPath, "utf-8")) as Record<
        string,
        unknown
      >;
      const labId =
        typeof raw.labId === "string" && isLabId(raw.labId)
          ? raw.labId.trim()
          : entry.name;
      const title =
        typeof raw.title === "string" && raw.title.trim()
          ? raw.title.trim()
          : labId;
      const chapterCode =
        typeof raw.chapterCode === "string" ? raw.chapterCode.trim() : "";
      const unitsUsed = Array.isArray(raw.unitsUsed)
        ? raw.unitsUsed.filter((u): u is string => typeof u === "string")
        : [];
      const unitCode =
        (typeof raw.unitCode === "string" && raw.unitCode.trim()) ||
        chapterCode ||
        unitsUsed[0] ||
        "";
      const topicCode =
        (typeof raw.topicCode === "string" && raw.topicCode.trim()) ||
        (chapterCode ? chapterCode.split("-").slice(0, 2).join("-") : "");
      const kind =
        typeof raw.kind === "string" && raw.kind.trim()
          ? raw.kind.trim()
          : "chapter-lab";
      const level = typeof raw.level === "number" ? raw.level : undefined;
      const rawMilestones = Array.isArray(raw.milestones)
        ? (raw.milestones as Array<{ id?: string }>)
        : [];

      const progressFile = readProgress(labId);
      const progress = summarizeLabProgress(rawMilestones, progressFile);
      const summaryMistakes = (progressFile?.sessionSummary as { mistakeCategories?: unknown } | undefined)
        ?.mistakeCategories;
      const hasNotes =
        rawMilestones.some((ms) => {
          const mid = String(ms.id || "").trim();
          if (!mid) return false;
          const st = makeDefaultMilestoneState(lookupStateForMilestone(progressFile?.problems, mid));
          return Boolean(st.mistakeNote && st.mistakeNote.trim()) || st.mistakes.length > 0;
        }) ||
        (Array.isArray(summaryMistakes) && summaryMistakes.length > 0);

      const chapterTitle =
        cleanCurriculumTitle(idMapTitles.get(chapterCode)) || chapterCode;
      const topicTitle =
        cleanCurriculumTitle(idMapTitles.get(topicCode)) || topicCode;

      items.push({
        id: labId,
        labId,
        title,
        unitCode,
        chapterCode,
        chapterTitle,
        topicCode,
        topicTitle,
        unitsUsed: unitsUsed.length > 0 ? unitsUsed : unitCode ? [unitCode] : [],
        kind,
        level,
        milestoneCount: rawMilestones.length,
        practiceStatus: progress.practiceStatus,
        passedCount: progress.passedCount,
        reviseCount: progress.reviseCount,
        score: progress.score,
        maxScore: progress.maxScore,
        hasNotes,
        progress,
      });
    } catch {
      continue;
    }
  }

  items.sort((a, b) => a.id.localeCompare(b.id));
  return items;
}

/**
 * Load a single project lab's redacted configuration, milestones, README, IDE links,
 * and per-milestone review state. Never reads or returns anything under `labs/_reference/`.
 */
export function loadLabDetailFromDisk(
  labId: string,
  labsDir: string = getLabsDir()
): LabDetailResponse | null {
  if (!isLabId(labId) || !isSafeId(labId)) return null;
  const trimmedId = labId.trim();
  if (trimmedId.startsWith("_") || trimmedId.includes("_reference")) return null;

  const labDir = path.resolve(labsDir, trimmedId);
  const relToLabs = path.relative(path.resolve(labsDir), labDir);
  if (
    !relToLabs ||
    relToLabs.startsWith("..") ||
    path.isAbsolute(relToLabs) ||
    relToLabs.split(/[\\/]+/).includes("_reference")
  ) {
    return null;
  }

  const configPath = path.join(labDir, "lab.config.json");
  if (!fs.existsSync(configPath)) return null;

  let rawConfig: Record<string, unknown>;
  try {
    rawConfig = JSON.parse(fs.readFileSync(configPath, "utf-8")) as Record<
      string,
      unknown
    >;
  } catch {
    return null;
  }

  const readmePath = path.join(labDir, "README.md");
  const rawReadme = fs.existsSync(readmePath)
    ? fs.readFileSync(readmePath, "utf-8")
    : "";
  const readme = sanitizeLabReadme(rawReadme);
  const readmeMilestones = parseReadmeMilestones(readme);

  const canonicalId =
    typeof rawConfig.labId === "string" && isLabId(rawConfig.labId)
      ? rawConfig.labId.trim()
      : trimmedId;
  const title =
    typeof rawConfig.title === "string" && rawConfig.title.trim()
      ? rawConfig.title.trim()
      : canonicalId;
  const chapterCode =
    typeof rawConfig.chapterCode === "string" ? rawConfig.chapterCode.trim() : "";
  const unitsUsed = Array.isArray(rawConfig.unitsUsed)
    ? rawConfig.unitsUsed.filter((u): u is string => typeof u === "string")
    : [];
  const unitCode =
    (typeof rawConfig.unitCode === "string" && rawConfig.unitCode.trim()) ||
    chapterCode ||
    unitsUsed[0] ||
    "";
  const topicCode =
    (typeof rawConfig.topicCode === "string" && rawConfig.topicCode.trim()) ||
    (chapterCode ? chapterCode.split("-").slice(0, 2).join("-") : "");
  const kind =
    typeof rawConfig.kind === "string" && rawConfig.kind.trim()
      ? rawConfig.kind.trim()
      : "chapter-lab";
  const level = typeof rawConfig.level === "number" ? rawConfig.level : 3;
  const domain =
    typeof rawConfig.domain === "string" ? rawConfig.domain.trim() : "";
  const scenario =
    typeof rawConfig.scenario === "string" ? rawConfig.scenario.trim() : "";

  const absLabDir = labDir.startsWith("/") ? labDir : `/${labDir}`;
  const vscodeFolderUrl = `vscode://file${absLabDir}`;
  const cursorFolderUrl = `cursor://file${absLabDir}`;

  const progressFile = readProgress(canonicalId);
  const rawMilestones = Array.isArray(rawConfig.milestones)
    ? (rawConfig.milestones as Array<Record<string, unknown>>)
    : [];

  const milestones: LabMilestoneDetail[] = rawMilestones.map((ms, idx) => {
    const mid =
      typeof ms.id === "string" && ms.id.trim()
        ? ms.id.trim()
        : `M${idx + 1}`;
    const mTitle =
      typeof ms.title === "string" && ms.title.trim()
        ? ms.title.trim()
        : `Milestone ${mid}`;
    const readmeDesc = readmeMilestones[mid.toUpperCase()] || "";
    const rawGoal = typeof ms.goal === "string" ? ms.goal.trim() : "";
    const rawDesc =
      typeof ms.description === "string" ? ms.description.trim() : "";
    const goal = rawGoal || readmeDesc || mTitle;
    const description = readmeDesc || rawDesc || goal;
    const units = Array.isArray(ms.units)
      ? ms.units.filter((u): u is string => typeof u === "string")
      : [];
    const points = typeof ms.points === "number" ? ms.points : undefined;

    const visibleTestFiles = resolveMilestoneVisibleTestFiles(labDir, ms);
    const visibleTests = extractVisibleTestCases(labDir, mid, visibleTestFiles);
    const lowerMid = mid.toLowerCase();
    const testCommand = `npm run test:${lowerMid}`;
    const checkCommand = `npm run check:${lowerMid}`;

    const { mainFile, vscodeUrl, cursorUrl } = resolveMilestoneMainFile(
      labDir,
      ms
    );

    const savedState = lookupStateForMilestone(progressFile?.problems, mid);
    const state = makeDefaultMilestoneState(savedState);
    const reviewStatus = deriveReviewStatus(state.reviews);

    return {
      id: mid,
      title: mTitle,
      goal,
      description,
      units,
      ...(points !== undefined ? { points } : {}),
      visibleTestFiles,
      visibleTests,
      testCommand,
      checkCommand,
      mainFile,
      vscodeFolderUrl,
      cursorFolderUrl,
      vscodeUrl,
      cursorUrl,
      reviewStatus,
      state,
    };
  });

  const progress = summarizeLabProgress(milestones, progressFile);
  const rawSummary = (progressFile?.sessionSummary || {}) as Partial<SessionSummary>;
  const sessionSummary: SessionSummary = {
    practiceStatus: progress.practiceStatus,
    score: progress.score,
    maxScore: progress.maxScore,
    accuracyPct:
      progress.maxScore > 0
        ? Math.round((progress.score / progress.maxScore) * 100)
        : 0,
    skippedCount: rawSummary.skippedCount ?? 0,
    skippedProblems: Array.isArray(rawSummary.skippedProblems)
      ? rawSummary.skippedProblems
      : [],
    mistakeCategories: Array.isArray(rawSummary.mistakeCategories)
      ? rawSummary.mistakeCategories
      : [],
    divergedStepsSummary:
      typeof rawSummary.divergedStepsSummary === "string"
        ? rawSummary.divergedStepsSummary
        : "",
    attemptDate:
      typeof rawSummary.attemptDate === "string" ? rawSummary.attemptDate : null,
    syncedToNotionAt:
      typeof rawSummary.syncedToNotionAt === "string"
        ? rawSummary.syncedToNotionAt
        : null,
    notionPageId:
      typeof rawSummary.notionPageId === "string"
        ? rawSummary.notionPageId
        : null,
  };

  return {
    id: canonicalId,
    labId: canonicalId,
    title,
    unitCode,
    chapterCode,
    topicCode,
    unitsUsed: unitsUsed.length > 0 ? unitsUsed : unitCode ? [unitCode] : [],
    kind,
    level,
    domain,
    scenario,
    readme,
    workspaceDir: labDir,
    vscodeFolderUrl,
    cursorFolderUrl,
    testCommand: "npm test",
    checkCommand: "npm run check",
    unitNotionUrl: resolveNotionUrlForLab(canonicalId, unitCode, chapterCode),
    milestones,
    progress,
    sessionSummary,
  };
}
