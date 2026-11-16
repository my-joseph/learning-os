import globals from "globals";
import tseslint from "typescript-eslint";

/**
 * Shared ESLint 9 flat config for PRG drills and labs.
 *
 * @param {object} [options]
 * @param {Array<{ rule: string, reason: string }>} [options.overrides]
 * @returns {Array<import("eslint").Linter.Config>}
 */
export function prgConfig({ overrides = [] } = {}) {
  if (!Array.isArray(overrides)) {
    throw new Error("prgConfig: 'overrides' must be an array of { rule, reason }");
  }

  const overrideRules = {};
  for (const entry of overrides) {
    if (!entry || typeof entry !== "object") {
      throw new Error("prgConfig: each override must be an object with { rule, reason }");
    }
    const { rule, reason } = entry;
    if (typeof rule !== "string" || rule.trim() === "") {
      throw new Error("prgConfig: override is missing a non-empty 'rule'");
    }
    if (typeof reason !== "string" || reason.trim() === "") {
      throw new Error(`prgConfig: override for '${rule}' must have a non-empty 'reason'`);
    }
    overrideRules[rule] = "off";
  }

  const config = [
    {
      ignores: ["**/node_modules/**", "**/dist/**"],
    },
    {
      files: ["**/*.{js,mjs,cjs,ts,tsx}"],
      languageOptions: {
        ecmaVersion: "latest",
        sourceType: "module",
        globals: {
          ...globals.node,
          ...globals.es2024,
        },
      },
      rules: {
        "no-var": "error",
        "prefer-const": "error",
        eqeqeq: "error",
        "no-unused-vars": [
          "error",
          {
            argsIgnorePattern: "^_",
            varsIgnorePattern: "^_",
            caughtErrorsIgnorePattern: "^_",
          },
        ],
        "no-param-reassign": ["error", { props: true }],
        "consistent-return": "error",
        "no-implicit-coercion": "error",
        "require-await": "error",
        "no-shadow": "error",
        "no-unreachable": "error",
        complexity: ["error", 8],
        "max-depth": ["error", 3],
        "max-params": ["error", 4],
        "max-lines-per-function": [
          "error",
          { max: 40, skipBlankLines: true, skipComments: true },
        ],
      },
    },
    {
      files: ["**/*.{ts,tsx}"],
      languageOptions: {
        parser: tseslint.parser,
        parserOptions: {
          projectService: {
            allowDefaultProject: ["*.ts", "*.tsx"],
            maximumDefaultProjectFileMatchCount_THIS_WILL_SLOW_DOWN_LINTING: 32,
          },
        },
      },
      plugins: {
        "@typescript-eslint": tseslint.plugin,
      },
      rules: {
        "no-unused-vars": "off",
        "@typescript-eslint/no-unused-vars": [
          "error",
          {
            argsIgnorePattern: "^_",
            varsIgnorePattern: "^_",
            caughtErrorsIgnorePattern: "^_",
          },
        ],
        "no-shadow": "off",
        "@typescript-eslint/no-shadow": "error",
        "@typescript-eslint/no-explicit-any": "error",
        "@typescript-eslint/no-floating-promises": [
          "error",
          {
            allowForKnownSafeCalls: [
              {
                from: "package",
                name: ["test", "describe", "it", "before", "after", "beforeEach", "afterEach"],
                package: "node:test",
              },
            ],
          },
        ],
        "@typescript-eslint/no-misused-promises": "error",
        // @typescript-eslint/strict-boolean-expressions: enabled per level later
      },
    },
    {
      files: ["**/*.test.*"],
      rules: {
        "max-lines-per-function": "off",
        "max-params": "off",
      },
    },
  ];

  if (Object.keys(overrideRules).length > 0) {
    config.push({ rules: overrideRules });
  }

  return config;
}
