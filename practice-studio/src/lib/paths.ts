import path from "path";
import fs from "fs";

/**
 * Returns the directory that holds `math_engine`, `drills/data`, and `.venv`.
 * Supports both standalone execution (inside practice-studio/) and parent repo execution.
 */
export function getWorkspaceRoot(): string {
  if (process.env.LEARNINGOS_ROOT) {
    return path.resolve(process.env.LEARNINGOS_ROOT);
  }
  const cwd = process.cwd();
  const parent = path.resolve(cwd, "..");

  // If parent contains both math_engine and code_engine, that is the true project root
  if (
    fs.existsSync(path.join(parent, "math_engine")) &&
    fs.existsSync(path.join(parent, "code_engine"))
  ) {
    return parent;
  }

  // Check if current directory has math_engine
  if (fs.existsSync(path.join(cwd, "math_engine"))) {
    return cwd;
  }

  return parent;
}

export function getDrillsDataDir(): string {
  if (process.env.DRILLS_DATA_DIR) {
    return path.resolve(process.env.DRILLS_DATA_DIR);
  }
  return path.join(getWorkspaceRoot(), "drills", "data");
}

/** Directory holding variant bank JSON files (`drills/variants/<UNIT>.json`). */
export function getVariantsDir(): string {
  if (process.env.VARIANTS_DIR) {
    return path.resolve(process.env.VARIANTS_DIR);
  }
  return path.join(getWorkspaceRoot(), "drills", "variants");
}

export function getLabsDir(): string {
  if (process.env.LABS_DIR) {
    return path.resolve(process.env.LABS_DIR);
  }
  return path.join(getWorkspaceRoot(), "labs");
}

export function getPythonBin(rootDir: string): string {
  const candidates = [
    path.join(rootDir, ".venv", "bin", "python"),
    path.join(rootDir, "practice-studio", ".venv", "bin", "python"),
    path.resolve(process.cwd(), "..", ".venv", "bin", "python"),
    path.resolve(process.cwd(), ".venv", "bin", "python"),
  ];
  for (const cand of candidates) {
    if (fs.existsSync(cand)) {
      return cand;
    }
  }
  return "python3";
}

export const JSON_EXTENSIONS = [".json"];
export const SOURCE_EXTENSIONS = [".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs"];

type ContainmentOptions =
  | { directory: true; allowMissing?: boolean }
  | { extensions: readonly string[]; allowMissing?: boolean };

/**
 * Resolve a relative path at its storage boundary. Existing components must
 * be real directories or regular files. A configured external root is an
 * explicit boundary, while roots inside the checkout are checked from its root.
 */
export function resolveContainedPath(
  rootDir: string,
  relativePath: string,
  options: ContainmentOptions
): string | null {
  const directory = "directory" in options;
  const parts = relativePath === "." && directory ? [] : relativePath.split("/");
  if (
    /[\\%:\0]/.test(relativePath) ||
    parts.some((part) =>
      !part || part === "." || part === ".." || part === "_reference" ||
      part === ".canonical" || part.startsWith(".env") || part.includes(".hidden.")
    ) ||
    (!directory && !options.extensions.includes(path.extname(relativePath)))
  ) {
    return null;
  }

  const boundary = path.resolve(rootDir);
  const checkout = getWorkspaceRoot();
  const withinCheckout = path.relative(checkout, boundary);
  const nested = withinCheckout && withinCheckout !== ".." &&
    !withinCheckout.startsWith(`..${path.sep}`) && !path.isAbsolute(withinCheckout);
  const anchor = nested ? checkout : boundary;
  const segments = nested ? [...withinCheckout.split(path.sep), ...parts] : parts;
  let resolved = anchor;
  let missing = false;

  try {
    for (let i = -1; i < segments.length; i++) {
      if (i >= 0) resolved = path.join(resolved, segments[i]);
      if (missing) continue;
      try {
        const info = fs.lstatSync(resolved);
        const isDirectory = directory || i < segments.length - 1;
        if (isDirectory ? !info.isDirectory() : !info.isFile()) return null;
        if (i === -1) resolved = fs.realpathSync(resolved);
      } catch (err) {
        if (!options.allowMissing || (err as NodeJS.ErrnoException).code !== "ENOENT") {
          return null;
        }
        missing = true;
      }
    }
    return resolved;
  } catch {
    return null;
  }
}

/** Validates an ID used as a path segment (drillId, unitCode). */
export function isSafeId(value: unknown): value is string {
  return typeof value === "string" && /^[A-Za-z0-9][A-Za-z0-9_-]{0,127}$/.test(value);
}

/** Validates a canonical local MTH, PHY, or PRG drill ID (never a LAB or path ID). */
export function isCanonicalDrillId(value: unknown): value is string {
  return (
    typeof value === "string" &&
    /^DRL-(?:MTH|PHY|PRG)-[A-Z0-9]+(?:-[A-Z0-9]+)*$/.test(value)
  );
}

/** True when LEARNINGOS_PILOT is enabled ('1', 'true', 'yes'); mirrors progress_store.pilot_mode(). */
export function isPilotMode(): boolean {
  const pilot = (process.env.LEARNINGOS_PILOT || "").trim().toLowerCase();
  return pilot === "1" || pilot === "true" || pilot === "yes";
}

/** Base directory holding materialized drill workspaces (`pilot/workspace` in pilot mode, else `drills/workspace`). */
export function getDrillWorkspacesDir(rootDir: string = getWorkspaceRoot()): string {
  const sub = isPilotMode()
    ? path.join("pilot", "workspace")
    : path.join("drills", "workspace");
  return path.resolve(rootDir, sub);
}

/** Materialized workspace directory for a single drill (`<wsBase>/<drillId>`). */
export function getDrillWorkspaceDir(
  drillId: string,
  rootDir: string = getWorkspaceRoot()
): string | null {
  if (!isSafeId(drillId)) return null;
  return path.join(getDrillWorkspacesDir(rootDir), drillId);
}

/** Base directory holding active project lab workspaces (`LABS_DIR`, else `pilot/labs` in pilot mode, else `labs`). */
export function getLabWorkspacesDir(rootDir: string = getWorkspaceRoot()): string {
  if (process.env.LABS_DIR) {
    return path.resolve(process.env.LABS_DIR);
  }
  const sub = isPilotMode() ? path.join("pilot", "labs") : "labs";
  return path.resolve(rootDir, sub);
}

/** Active workspace directory for a single lab (`<labWsBase>/<labId>`). */
export function getLabWorkspaceDir(
  labId: string,
  rootDir: string = getWorkspaceRoot()
): string | null {
  if (!isSafeId(labId)) return null;
  return path.join(getLabWorkspacesDir(rootDir), labId);
}

/**
 * Maps a relative workspace file path (`drills/workspace/<drillId>/...` or
 * `pilot/workspace/<drillId>/...`) to the active workspace directory for the
 * current mode (`pilot/workspace/<drillId>/...` in pilot mode, else
 * `drills/workspace/<drillId>/...`). Leaves other paths unchanged so
 * traversal/escape checks can reject them.
 */
export function remapWorkspaceFileForMode(
  relOrAbs: string,
  drillId: string
): string {
  if (typeof relOrAbs !== "string" || !isSafeId(drillId)) return relOrAbs;
  const trimmed = relOrAbs.trim();
  if (!trimmed || path.isAbsolute(trimmed)) return relOrAbs;
  const normalized = trimmed.replace(/\\/g, "/").replace(/^\.\/+/, "");
  const activePrefix = isPilotMode()
    ? `pilot/workspace/${drillId}/`
    : `drills/workspace/${drillId}/`;
  const altPrefix = isPilotMode()
    ? `drills/workspace/${drillId}/`
    : `pilot/workspace/${drillId}/`;
  if (normalized.startsWith(altPrefix)) {
    return activePrefix + normalized.slice(altPrefix.length);
  }
  return relOrAbs;
}

/** Resolve a manifest or request path inside the active workspace for this drill. */
export function resolveInsideDrillWorkspace(
  workspaceFile: string,
  drillId: string,
  rootDir: string = getWorkspaceRoot()
): string | null {
  const wsDir = getDrillWorkspaceDir(drillId, rootDir);
  if (!wsDir || typeof workspaceFile !== "string") return null;
  const mapped = remapWorkspaceFileForMode(workspaceFile, drillId).replace(/\\/g, "/");
  const prefix = path.relative(rootDir, wsDir).split(path.sep).join("/") + "/";
  if (!mapped.startsWith(prefix)) return null;
  return resolveContainedPath(wsDir, mapped.slice(prefix.length), {
    extensions: SOURCE_EXTENSIONS,
    allowMissing: true,
  });
}

/** Where learner progress lives (progress/<DRILL_ID>.json); mirrors progress_store.py. */
export function getProgressDir(): string {
  if (process.env.PROGRESS_DIR) {
    return path.resolve(process.env.PROGRESS_DIR);
  }
  if (isPilotMode()) {
    return path.join(getWorkspaceRoot(), "pilot", "progress");
  }
  return path.join(getWorkspaceRoot(), "progress");
}

/** Enumerate regular JSON files below the drill data root, without following symlinks. */
export function listDrillFiles(
  dataDir = getDrillsDataDir(),
  recursive = false
): string[] {
  const files: string[] = [];

  function visit(relativeDir: string, depth: number): void {
    const dir = resolveContainedPath(dataDir, relativeDir || ".", { directory: true });
    if (!dir) return;
    for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
      const relativeFile = relativeDir ? `${relativeDir}/${entry.name}` : entry.name;
      if (entry.isDirectory() && (depth === 0 || recursive)) {
        visit(relativeFile, depth + 1);
      } else if (entry.isFile() && (depth === 1 || recursive)) {
        const candidate = resolveContainedPath(dataDir, relativeFile, { extensions: JSON_EXTENSIONS });
        if (candidate) files.push(candidate);
      }
    }
  }

  visit("", 0);
  return files;
}

function findDirectDrillFiles(drillId: string, dataDir: string): string[] {
  const root = resolveContainedPath(dataDir, ".", { directory: true });
  if (!root) return [];
  const matches: string[] = [];
  for (const entry of fs.readdirSync(root, { withFileTypes: true })) {
    if (!entry.isDirectory()) continue;
    const candidate = resolveContainedPath(dataDir, `${entry.name}/${drillId}.json`, {
      extensions: JSON_EXTENSIONS,
    });
    if (candidate) matches.push(candidate);
  }
  return matches;
}

function findDrillFilePath(drillId: string, dataDir = getDrillsDataDir()): string | null {
  if (!isSafeId(drillId)) return null;
  return findDirectDrillFiles(drillId, dataDir)[0] ??
    listDrillFiles(dataDir, true).find((candidate) => path.basename(candidate) === `${drillId}.json`) ??
    null;
}

/** Locate the canonical content file for one validated local drill ID. */
export function findCanonicalDrillFilePath(drillId: string): string | null {
  if (!isCanonicalDrillId(drillId)) return null;
  const matches: string[] = [];
  for (const candidate of findDirectDrillFiles(drillId, getDrillsDataDir())) {
    try {
      const doc = JSON.parse(fs.readFileSync(candidate, "utf-8")) as Record<string, unknown>;
      const domain = drillId.split("-")[1];
      if (
        doc &&
        typeof doc === "object" &&
        doc.drillId === drillId &&
        typeof doc.unitCode === "string" &&
        doc.unitCode.startsWith(`${domain}-`) &&
        path.basename(path.dirname(candidate)) === doc.unitCode
      ) {
        matches.push(candidate);
      }
    } catch {
      // A malformed document is not a canonical target and must not be deleted.
    }
  }
  return matches.length === 1 ? matches[0] : null;
}

/** Load an unredacted canonical drill document from drills/data on the server. */
export function loadDrillFromDisk(drillId: string): Record<string, unknown> | null {
  const filePath = findDrillFilePath(drillId);
  if (!filePath) return null;
  try {
    const doc = JSON.parse(fs.readFileSync(filePath, "utf-8")) as Record<string, unknown>;
    if (!doc || typeof doc !== "object" || Array.isArray(doc)) return null;
    if (doc.drillId && doc.drillId !== drillId) return null;
    return { ...doc, drillId };
  } catch {
    return null;
  }
}

/** Load a specific problem and its parent drill document from drills/data on the server. */
export function loadProblemFromDisk(
  drillId: string,
  problemId: string
): { doc: Record<string, unknown>; problem: Record<string, unknown> } | null {
  if (!isSafeId(drillId) || !isSafeId(problemId)) return null;
  const doc = loadDrillFromDisk(drillId);
  if (!doc || !Array.isArray(doc.problems)) return null;
  const problem = (doc.problems as Array<Record<string, unknown>>).find(
    (p) => p && typeof p === "object" && p.id === problemId
  );
  if (!problem) return null;
  return { doc, problem };
}

/** Load an unredacted variant bank JSON file (`drills/variants/<unitCode>.json`) on the server. */
export function loadVariantBankFromDisk(
  unitCode: string
): { unitCode: string; variants: Array<Record<string, unknown>> } | null {
  if (!isSafeId(unitCode)) return null;
  const filePath = resolveContainedPath(getVariantsDir(), `${unitCode}.json`, {
    extensions: JSON_EXTENSIONS,
  });
  if (!filePath) return null;
  try {
    const raw = JSON.parse(fs.readFileSync(filePath, "utf-8")) as Record<string, unknown>;
    if (!raw || typeof raw !== "object" || !Array.isArray(raw.variants)) return null;
    return {
      unitCode: typeof raw.unitCode === "string" ? raw.unitCode : unitCode,
      variants: raw.variants.filter(
        (v): v is Record<string, unknown> => Boolean(v && typeof v === "object")
      ),
    };
  } catch {
    return null;
  }
}

/** Locate an unredacted variant by `variantId` across `drills/variants/*.json` on the server. */
export function loadVariantFromDisk(
  variantId: string
): { unitCode: string; variant: Record<string, unknown> } | null {
  if (!isSafeId(variantId)) return null;
  const dir = resolveContainedPath(getVariantsDir(), ".", { directory: true });
  if (!dir) return null;

  const files = fs
    .readdirSync(dir)
    .filter((f) => f.endsWith(".json"))
    .sort();

  // Prefer the bank whose unitCode matches the prefix after "VAR-".
  if (variantId.startsWith("VAR-")) {
    const tail = variantId.slice(4);
    files.sort((a, b) => {
      const aMatch = tail.startsWith(a.slice(0, -5) + "-") ? 0 : 1;
      const bMatch = tail.startsWith(b.slice(0, -5) + "-") ? 0 : 1;
      return aMatch - bMatch || a.localeCompare(b);
    });
  }

  for (const file of files) {
    const unitCode = file.slice(0, -5);
    const bank = loadVariantBankFromDisk(unitCode);
    if (!bank) continue;
    const match = bank.variants.find((v) => v.variantId === variantId);
    if (match) {
      return { unitCode: bank.unitCode, variant: match };
    }
  }
  return null;
}

/** Load curriculum code -> title mappings from `id_map.json` at the workspace root. */
export function loadIdMapTitles(rootDir: string = getWorkspaceRoot()): Map<string, string> {
  const titles = new Map<string, string>();
  const idMapPath = resolveContainedPath(rootDir, "id_map.json", { extensions: JSON_EXTENSIONS });
  if (!idMapPath) return titles;
  try {
    const raw = JSON.parse(fs.readFileSync(idMapPath, "utf-8")) as Record<string, unknown>;
    for (const [key, val] of Object.entries(raw)) {
      if (val && typeof val === "object" && typeof (val as { title?: unknown }).title === "string") {
        titles.set(key, (val as { title: string }).title);
      }
    }
  } catch {
    return titles;
  }
  return titles;
}
