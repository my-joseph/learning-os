/**
 * Automated Verification Suite for PRG-T03-C01-U01 (Next.js Project Structure & Environment Boundaries)
 * Drill ID: DRL-PRG-T03-C01-U01-01
 */

export type NodeEnvMode = "development" | "production" | "test";

export interface EnvFiles {
  processEnv?: Record<string, string>;
  envLocal?: Record<string, string>;
  envModeLocal?: Record<string, string>;
  envMode?: Record<string, string>;
  envBase?: Record<string, string>;
}

/**
 * Resolves Next.js environment variable priority exactly as next/env does:
 * 1. process.env
 * 2. .env.$(NODE_ENV).local
 * 3. .env.local (SKIPPED when NODE_ENV === 'test')
 * 4. .env.$(NODE_ENV)
 * 5. .env
 */
export function resolveNextEnvVar(key: string, mode: NodeEnvMode, files: EnvFiles): string | undefined {
  if (files.processEnv && key in files.processEnv) return files.processEnv[key];
  if (files.envModeLocal && key in files.envModeLocal) return files.envModeLocal[key];
  if (mode !== "test" && files.envLocal && key in files.envLocal) return files.envLocal[key];
  if (files.envMode && key in files.envMode) return files.envMode[key];
  if (files.envBase && key in files.envBase) return files.envBase[key];
  return undefined;
}

/**
 * Verifies whether an environment variable is exposed to the browser bundle.
 */
export function isClientExposedEnv(varName: string, isStaticDotAccess: boolean): boolean {
  return varName.startsWith("NEXT_PUBLIC_") && isStaticDotAccess;
}

// Self-verification assertions
const devVal = resolveNextEnvVar("API_TIMEOUT", "development", {
  envBase: { API_TIMEOUT: "3000" },
  envMode: { API_TIMEOUT: "5000" },
  envLocal: { API_TIMEOUT: "1000" },
});
if (devVal !== "1000") throw new Error(`Expected 1000 in development, got ${devVal}`);

const testVal = resolveNextEnvVar("API_TIMEOUT", "test", {
  envBase: { API_TIMEOUT: "3000" },
  envMode: { API_TIMEOUT: "5000" },
  envLocal: { API_TIMEOUT: "1000" },
});
if (testVal !== "5000") throw new Error(`Expected 5000 in test (.env.local skipped), got ${testVal}`);
