# -*- coding: utf-8 -*-
"""
Builder module for PRG-T00-C03 (Developer Workflow & Git):
Generates production-grade, Gold Standard (v3) content for:
- PRG-T00-C03 (Chapter: Developer Workflow & Git)
- PRG-T00-C03-U01 through U06 (6 Units)

Strictly adheres to Central Rules:
- Complete Practice Guide (Core Skills, Prior Units, Common Traps, Cross-Subject Connections)
- Active Recall Questions with toggles
- My Implementation & Mistake Log
- Native @Page mentions (zero unparsed [[ tokens)
- 100% English, zero markdown leaks
"""
import json
import re
from apply_rules_and_test_pages import (
    h2,
    h3,
    p_block,
    callout_block,
    quote_block,
    bullet,
    num_item,
    todo_item,
    toggle_block,
    code_block,
    divider_block,
)

def build_prg_t00_c03(id_map):
    return [
        callout_block(
            "**Chapter Objective:** Establish professional software engineering workflow literacy across the terminal command-line interface, project hierarchy, npm dependency management, Git distributed version control, and collaborative pull request review cycles.\n"
            "**Completion Criteria:** Initialize a project from the terminal, configure automated scripts in `package.json`, enforce `.gitignore` hygiene, manage Git feature branches with conventional commits, resolve merge conflicts, and submit a documented pull request with test telemetry.\n"
            "**Parent Topic:** [[PRG-T00]] | **Sources:** [[R029]] (`Pro Git Book by Scott Chacon`), [[R003]] (`MDN JS Guide`)",
            id_map,
            color="blue_background",
        ),
        h2("1. Chapter Role & Professional Engineering Workflow Mental Model", id_map),
        p_block(
            "[[PRG-T00-C03]] establishes the operational foundation for all modern software development. Code does not exist in an isolated text editor; it lives in a structured file system, depends on third-party packages, is verified by automated test pipelines, and evolves through version-controlled team collaboration:",
            id_map,
        ),
        num_item(
            "**Unix Philosophy & Terminal Agility:** The CLI is the primary cockpit of software engineering. Composable commands, standard input/output streams, redirection, and environment variables allow developers to automate builds, inspect system state, and orchestrate runtimes efficiently.",
            id_map,
        ),
        num_item(
            "**Deterministic Dependency Trees:** The `package.json` manifest and `package-lock.json` lockfile ensure that application dependencies are reproducible across different machines, continuous integration servers, and production deployments.",
            id_map,
        ),
        num_item(
            "**Directed Acyclic Graph (DAG) Version Control:** Git records changes not as file differences, but as immutable snapshots forming a cryptographic graph. Branches are lightweight pointers to commits, enabling non-destructive experimentation and collaborative parallel development.",
            id_map,
        ),
        num_item(
            "**Asynchronous Code Review & CI Automation:** Professional teams gate production changes behind automated test verification (`npm test`, `npm run submit`) and peer pull request reviews. Code reviews preserve architectural standards, catch boundary bugs, and share domain knowledge.",
            id_map,
        ),
        divider_block(),
        h2("2. Core Engineering Invariants", id_map),
        bullet("**Zero Unversioned Secrets:** Never commit `.env`, API credentials, private certificates, or local machine configurations to version control. Always maintain a strict `.gitignore`.", id_map),
        bullet("**Atomic & Conventional Commits:** Every commit must represent a single logical change with a descriptive prefix (`feat:`, `fix:`, `refactor:`, `test:`, `docs:`). Avoid massive 'WIP' commits.", id_map),
        bullet("**Verification Before Merge:** Never merge branches or submit PRs without running test suites locally (`npm test`). Green tests are the non-negotiable contract of shipping software.", id_map),
        divider_block(),
        h2("3. Learning Units in this Chapter (6 Units)", id_map),
        num_item("[[PRG-T00-C03-U01]] — **Terminal and Project Structure:** Shell navigation, paths, file operations, standard streams, pipes, and standard software project directory layouts.", id_map),
        num_item("[[PRG-T00-C03-U02]] — **npm and Package Scripts:** Manifest anatomy, SemVer, deterministic lockfiles, lifecycle scripts (`test`, `review`, `submit`), and dependency management.", id_map),
        num_item("[[PRG-T00-C03-U03]] — **Git Repository Basics:** Repository initialization, three-tier state architecture (working tree, index, history), `.gitignore` patterns, and commit inspection.", id_map),
        num_item("[[PRG-T00-C03-U04]] — **Branches, Commits and Merge:** Feature branch workflows, conventional commits, fast-forward vs merge commits, and systematic conflict resolution.", id_map),
        num_item("[[PRG-T00-C03-U05]] — **GitHub Workflow and Pull Requests:** Remote tracking branches, pull request authoring, CI automation gates, and code review feedback loops.", id_map),
        num_item("[[PRG-T00-C03-U06]] — **README and Issue Tracking:** Architectural documentation, reproduction steps, issue bug triage, and Architectural Decision Records (ADRs).", id_map),
        divider_block(),
        h2("4. Chapter Capstone Practice Blueprint", id_map),
        p_block("After studying the 6 Units in [[PRG-T00-C03]], execute this real-world developer workflow blueprint:", id_map),
        bullet("**Task:** From an empty terminal directory, initialize a Git repository, configure an npm package with automated test and review scripts, create a feature branch, resolve an intentional merge conflict, and document the project with a production README.", id_map),
        bullet("**Invariants to Enforce:**", id_map, children=[
            bullet("Use terminal commands exclusively (`mkdir`, `cd`, `touch`, `npm init`, `git ...`).", id_map),
            bullet("Enforce `.gitignore` excluding `node_modules/`, `.env`, and test artifacts.", id_map),
            bullet("Configure `package.json` with scripts: `test`, `review`, and `submit`.", id_map),
            bullet("Write at least 3 atomic commits following the Conventional Commits specification.", id_map),
            bullet("Create a merge conflict intentionally between `main` and a feature branch, resolve it manually, and verify test suite passes.", id_map),
        ]),
        divider_block(),
        h2("5. Verification & Mastery Checklist", id_map),
        todo_item("Pass all 6 Units from [[PRG-T00-C03-U01]] to [[PRG-T00-C03-U06]] with honest Mastery >= 3.", id_map),
        todo_item("Explain the exact difference between the Working Directory, the Staging Area (Index), and Git Object Storage (`HEAD`).", id_map),
        todo_item("Demonstrate how `package-lock.json` guarantees reproducible builds across distributed engineering teams.", id_map),
    ]


def build_prg_t00_c03_u01(id_map):
    return [
        callout_block(
            "**Learning Objective:** Master the Unix terminal shell environment, file system navigation, relative vs absolute paths, file manipulation commands, input/output streams, redirection, piping, and professional project directory layouts.\n"
            "**Expected Output:** Confidently navigate, manipulate files, inspect system state, and assemble robust directory architectures from the command line without graphical file explorers.\n"
            "**Parent:** [[PRG-T00]] → [[PRG-T00-C03]] | **Next Unit:** [[PRG-T00-C03-U02]] | **Source:** [[R029]] (`Pro Git Book`)",
            id_map,
            color="blue_background",
        ),
        h2("1. Terminal Architecture & File System Mental Model", id_map),
        num_item(
            "**Shell vs Terminal:** The terminal emulator (e.g. iTerm2, macOS Terminal, VS Code integrated terminal) is the graphical display window. The shell (e.g. `zsh`, `bash`) is the command language interpreter that reads text commands, executes system calls, and manages processes.",
            id_map,
        ),
        num_item(
            "**Path Hierarchy & Traversal:** Every file exists in a hierarchical tree rooted at `/`. Absolute paths specify the complete location from root (`/Users/developer/project`). Relative paths evaluate relative to the current working directory (`.` is current directory, `..` is parent directory, `~` is user home directory).",
            id_map,
        ),
        num_item(
            "**Standard Streams & Composition:** Unix programs communicate via three standard I/O byte streams: `stdin` (fd 0, standard input), `stdout` (fd 1, standard output), and `stderr` (fd 2, standard error). Streams can be redirected (`>`, `>>`, `2>&1`) or piped (`|`) to compose powerful one-line utility pipelines.",
            id_map,
        ),
        divider_block(),
        h2("2. Core Terminal Commands & Directory Patterns", id_map),
        code_block(
            "# 1. Navigation & Path Inspection\n"
            "pwd                     # Print working directory\n"
            "ls -la                  # List all files including hidden dotfiles with permissions\n"
            "cd src/components       # Relative traversal\n"
            "cd ../..                # Navigate up two directory levels\n"
            "\n"
            "# 2. Safe File & Directory Operations\n"
            "mkdir -p src/{utils,services} # Create parent and nested directory hierarchies\n"
            "touch src/index.ts      # Create empty file or update timestamp\n"
            "cp -r src/ backup-src/  # Recursive directory copy\n"
            "mv temp.ts src/temp.ts  # Move or rename file\n"
            "\n"
            "# 3. Stream Redirection and Piping\n"
            "node app.js > build.log 2>&1  # Redirect both stdout and stderr to file\n"
            "cat server.log | grep \"ERROR\" | wc -l # Pipeline: count error lines",
            "shell",
        ),
        p_block(
            "Standard Production Project Hierarchy:\n"
            "• `src/` — Primary application source code.\n"
            "• `tests/` — Automated unit, integration, and end-to-end tests.\n"
            "• `dist/` or `build/` — Compiled output artifacts (never committed to Git).\n"
            "• `docs/` — Architectural documentation and diagrams.\n"
            "• `.gitignore` & `package.json` — Root configuration and dependency manifests.",
            id_map,
        ),
        divider_block(),
        h2("3. Complete Practice Guide", id_map),
        bullet("**Core Skills:** Navigating nested folders via relative paths, using `mkdir -p` to scaffold modules, piping logs through grep to diagnose server errors, and inspecting exit codes (`echo $?`).", id_map),
        bullet("**Prior Units:** Complements [[PRG-T00-C01-U08]] (DevTools) by moving diagnostic inspection from browser GUI to local OS runtime.", id_map),
        bullet("**Common Traps:**", id_map, children=[
            bullet("Accidental destruction using `rm -rf *` without checking `pwd` first.", id_map),
            bullet("Unquoted paths containing spaces causing shell arguments to split unexpectedly.", id_map),
            bullet("Confusing overwrite redirection (`>`) with append redirection (`>>`), destroying existing log files.", id_map),
        ]),
        bullet("**Cross-Subject Connections:** Directly utilized in [[PRG-T00-C03-U02]] for running npm lifecycle scripts and in [[PRG-T01]] through [[PRG-T05]] across all local development cockpits.", id_map),
        divider_block(),
        h2("4. Active Recall Questions", id_map),
        toggle_block(
            "Q1: What is the exact difference between `>` and `>>` when redirecting command output?",
            [p_block("`>` overwrites the destination file completely from byte 0, destroying any prior contents. `>>` appends new output to the end of the destination file while preserving existing data.", id_map)],
            id_map,
        ),
        toggle_block(
            "Q2: How does a shell pipe (`|`) connect two independent processes?",
            [p_block("The pipe connects the `stdout` (standard output) file descriptor of the program on the left directly into the `stdin` (standard input) file descriptor of the program on the right in memory, without creating intermediate temporary files on disk.", id_map)],
            id_map,
        ),
        toggle_block(
            "Q3: Why is `mkdir -p` safer and more convenient than plain `mkdir` in deployment scripts?",
            [p_block("`-p` (parents) creates any missing intermediate directories along the specified path without failing, and silently succeeds if the target directory already exists instead of throwing an error.", id_map)],
            id_map,
        ),
        divider_block(),
        h2("5. My Implementation & Mistake Log", id_map),
        todo_item("Open terminal and scaffold a complete project directory structure with `src/`, `tests/`, and `.gitignore` using only CLI commands.", id_map),
        todo_item("Inspect environment variables using `env` and explain what `$PATH` does when typing commands like `node` or `git`.", id_map),
        quote_block("Document any path traversal mistakes, missing flags, or stream redirection misunderstandings encountered during CLI exercises.", id_map),
    ]


def build_prg_t00_c03_u02(id_map):
    return [
        callout_block(
            "**Learning Objective:** Master the Node Package Manager (`npm`) ecosystem: `package.json` manifest structure, SemVer rules, deterministic `package-lock.json`, dependencies vs devDependencies, and custom package lifecycle scripts (`test`, `review`, `submit`).\n"
            "**Expected Output:** Configure and maintain production-ready `package.json` manifests, execute automated testing and code review workflows, and manage reproducible dependency graphs.\n"
            "**Parent:** [[PRG-T00]] → [[PRG-T00-C03]] | **Prior Unit:** [[PRG-T00-C03-U01]] | **Next Unit:** [[PRG-T00-C03-U03]] | **Source:** [[R003]] (`MDN JS Guide`)",
            id_map,
            color="blue_background",
        ),
        h2("1. Package Ecosystem & Dependency Resolution Mental Model", id_map),
        num_item(
            "**Manifest Contract (`package.json`):** The central configuration file defining project metadata, entrypoints, script automations, and external module requirements.",
            id_map,
        ),
        num_item(
            "**Semantic Versioning (SemVer):** Format `MAJOR.MINOR.PATCH`:\n"
            "• `MAJOR` introduces breaking, incompatible API changes.\n"
            "• `MINOR` adds backward-compatible features.\n"
            "• `PATCH` provides backward-compatible bug fixes.\n"
            "• Caret `^1.2.3` permits updates that do not modify the leftmost non-zero digit (e.g. `< 2.0.0`). Tilde `~1.2.3` permits only patch updates (`< 1.3.0`).",
            id_map,
        ),
        num_item(
            "**Deterministic Lockfile (`package-lock.json`):** Locks the exact resolved version, integrity hash, and nested dependency tree for every installed package. Must ALWAYS be committed to Git to prevent 'works on my machine' divergence.",
            id_map,
        ),
        num_item(
            "**Dependencies vs devDependencies:** `dependencies` are required for runtime production execution (e.g. web frameworks, database drivers). `devDependencies` are development-time only tools (e.g. compilers, test runners, linters, TypeScript definitions).",
            id_map,
        ),
        divider_block(),
        h2("2. Production Package Manifest & Automated Script Hooks", id_map),
        code_block(
            "{\n"
            "  \"name\": \"utility-toolkit\",\n"
            "  \"version\": \"1.0.0\",\n"
            "  \"private\": true,\n"
            "  \"scripts\": {\n"
            "    \"build\": \"tsc\",\n"
            "    \"test\": \"node --test tests/*.test.js\",\n"
            "    \"test:watch\": \"node --test --watch tests/*.test.js\",\n"
            "    \"review\": \"python3 ../../../code_engine/review.py\",\n"
            "    \"submit\": \"python3 ../../../code_engine/submit.py\"\n"
            "  },\n"
            "  \"dependencies\": {\n"
            "    \"dotenv\": \"^16.4.5\"\n"
            "  },\n"
            "  \"devDependencies\": {\n"
            "    \"@types/node\": \"^20.11.0\",\n"
            "    \"typescript\": \"^5.4.0\"\n"
            "  }\n"
            "}",
            "json",
        ),
        p_block(
            "Key npm execution mechanics:\n"
            "• `npm run <script>` runs the command inside an environment with `./node_modules/.bin` prepended to `$PATH`.\n"
            "• `npm test` and `npm start` are shorthand aliases that do not require the `run` keyword.\n"
            "• Passing flags through npm requires the `--` separator: `npm test -- --reporter=tap`.",
            id_map,
        ),
        divider_block(),
        h2("3. Complete Practice Guide", id_map),
        bullet("**Core Skills:** Creating `package.json` with `npm init -y`, installing runtime vs development dependencies (`--save-dev`), wiring automated testing scripts, and passing arguments to scripts using `--`.", id_map),
        bullet("**Prior Units:** Relies on [[PRG-T00-C03-U01]] terminal commands and links directly to [[PRG-T00-C02-U06]] for `tsc` build scripts.", id_map),
        bullet("**Common Traps:**", id_map, children=[
            bullet("Putting build tools (TypeScript, ESLint, test runners) into `dependencies` instead of `devDependencies`, inflating production Docker image sizes.", id_map),
            bullet("Deleting `package-lock.json` when encountering dependency conflicts instead of diagnosing the conflicting peer dependency version.", id_map),
            bullet("Committing `node_modules/` to Git repository (must always be in `.gitignore`).", id_map),
        ]),
        bullet("**Cross-Subject Connections:** Directly drives the practice and drill execution cockpit across all topics (`npm test`, `npm run review`, `npm run submit`).", id_map),
        divider_block(),
        h2("4. Active Recall Questions", id_map),
        toggle_block(
            "Q1: Why is `package-lock.json` essential in production software teams?",
            [p_block("`package.json` often uses ranges like `^1.2.0`. Without a lockfile, two developers running `npm install` on different days might install different minor versions, leading to unreproducible builds and subtle production runtime defects. `package-lock.json` records the exact SHA-512 cryptographic hash and specific version installed.", id_map)],
            id_map,
        ),
        toggle_block(
            "Q2: How does `npm install` distinguish between `dependencies` and `devDependencies` during production deployments?",
            [p_block("Running `npm install --omit=dev` (or setting `NODE_ENV=production`) skips all packages declared in `devDependencies`, significantly reducing artifact size and surface area in production environments.", id_map)],
            id_map,
        ),
        toggle_block(
            "Q3: Why does running `npm test` execute local binary binaries in `node_modules/.bin` without global installation?",
            [p_block("npm temporarily adds `./node_modules/.bin` to the beginning of the process `$PATH` during script execution, allowing locally installed CLI tools to take precedence over any globally installed binaries.", id_map)],
            id_map,
        ),
        divider_block(),
        h2("5. My Implementation & Mistake Log", id_map),
        todo_item("Configure a local `package.json` with `test`, `review`, and `submit` scripts and verify they execute correctly.", id_map),
        todo_item("Inspect the differences between `npm install <pkg>` and `npm install -D <pkg>` in the manifest file.", id_map),
        quote_block("Record any lockfile merge conflicts, SemVer caret/tilde confusion, or script execution errors encountered.", id_map),
    ]


def build_prg_t00_c03_u03(id_map):
    return [
        callout_block(
            "**Learning Objective:** Master foundational Git version control: repository initialization (`git init`), the three-tier state architecture (Working Tree, Staging Area, History), `.gitignore` syntax rules, patch-level staging (`git add -p`), and commit inspection.\n"
            "**Expected Output:** Initialize clean Git repositories, craft precise staged changes, exclude sensitive and generated files via `.gitignore`, and inspect repository commit logs.\n"
            "**Parent:** [[PRG-T00]] → [[PRG-T00-C03]] | **Prior Unit:** [[PRG-T00-C03-U02]] | **Next Unit:** [[PRG-T00-C03-U04]] | **Source:** [[R029]] (`Pro Git Book`)",
            id_map,
            color="blue_background",
        ),
        h2("1. Git Internal Model: The Three Trees", id_map),
        p_block(
            "Git does not track file deltas; it records snapshots of the entire repository object graph. Understanding Git requires understanding its three distinct areas:",
            id_map,
        ),
        num_item(
            "**The Working Directory (Working Tree):** The local filesystem files you see and edit directly. Changes here are uncommitted and unversioned.",
            id_map,
        ),
        num_item(
            "**The Staging Area (Index):** The preparation buffer where you assemble the exact changes destined for the next commit snapshot using `git add`.",
            id_map,
        ),
        num_item(
            "**The Repository (`HEAD` / Commit History):** The permanent object database in `.git/objects` storing cryptographically hashed (SHA-1 / SHA-256) commit objects, trees, and blobs.",
            id_map,
        ),
        divider_block(),
        h2("2. Core Git Workflow & `.gitignore` Architecture", id_map),
        code_block(
            "# 1. Initialize and inspect repository\n"
            "git init\n"
            "git status\n"
            "\n"
            "# 2. Configure .gitignore BEFORE staging files\n"
            "cat << 'EOF' > .gitignore\n"
            "# Dependencies\n"
            "node_modules/\n"
            "\n"
            "# Build outputs\n"
            "dist/\n"
            "build/\n"
            "\n"
            "# Environment secrets and local state\n"
            ".env\n"
            ".env.local\n"
            "*.log\n"
            ".DS_Store\n"
            "EOF\n"
            "\n"
            "# 3. Selective and patch staging\n"
            "git add .gitignore package.json\n"
            "git add -p src/index.ts       # Interactive staging of specific diff chunks\n"
            "git diff --staged             # Inspect changes staged in the index\n"
            "git commit -m \"chore: initial project configuration and gitignore\"",
            "shell",
        ),
        divider_block(),
        h2("3. Complete Practice Guide", id_map),
        bullet("**Core Skills:** Initializing Git repositories, configuring multi-pattern `.gitignore` files, staging changes atomically with `git add -p`, and reading `git status` output accurately.", id_map),
        bullet("**Prior Units:** Complements [[PRG-T00-C03-U01]] (CLI) and [[PRG-T00-C03-U02]] (ignoring `node_modules/`).", id_map),
        bullet("**Common Traps:**", id_map, children=[
            bullet("Adding files to `.gitignore` AFTER they have already been tracked by Git. Git will not ignore already-tracked files; you must run `git rm --cached <file>` first.", id_map),
            bullet("Running `git commit -a` blindly, staging unwanted debug statements or accidental file edits.", id_map),
            bullet("Committing private environment variables (`.env`) containing production API tokens or database secrets.", id_map),
        ]),
        bullet("**Cross-Subject Connections:** Invariant gate for all real-world engineering projects and CI/CD pipelines throughout the entire curriculum.", id_map),
        divider_block(),
        h2("4. Active Recall Questions", id_map),
        toggle_block(
            "Q1: What is the difference between `git diff` and `git diff --staged`?",
            [p_block("`git diff` displays changes between the Working Directory and the Staging Area (unstaged changes). `git diff --staged` (or `--cached`) displays changes between the Staging Area and the last commit in `HEAD` (what will go into the next commit).", id_map)],
            id_map,
        ),
        toggle_block(
            "Q2: If an engineer accidentally tracked `config.json` before adding it to `.gitignore`, how do they stop Git from tracking it without deleting the local file on disk?",
            [p_block("Execute `git rm --cached config.json` followed by a commit. This removes the file from the Git index while preserving the file in the local working directory.", id_map)],
            id_map,
        ),
        toggle_block(
            "Q3: Why is patch-level staging (`git add -p`) recommended over `git add .`?",
            [p_block("`git add -p` prompts the developer chunk by chunk (hunk), allowing them to review every diff before staging. This prevents temporary debug code, accidental whitespace edits, or unrelated changes from polluting an atomic commit.", id_map)],
            id_map,
        ),
        divider_block(),
        h2("5. My Implementation & Mistake Log", id_map),
        todo_item("Initialize a repository from scratch, verify untracked files are correctly excluded by `.gitignore`, and create an initial commit.", id_map),
        todo_item("Practice interactive staging with `git add -p` on a file with multiple disparate edits.", id_map),
        quote_block("Document any incidents where ignored files were tracked or accidental commits had to be reset.", id_map),
    ]


def build_prg_t00_c03_u04(id_map):
    return [
        callout_block(
            "**Learning Objective:** Master Git branching workflows, Conventional Commits specification, fast-forward vs 3-way merge mechanics, and systematic merge conflict diagnosis and resolution.\n"
            "**Expected Output:** Isolate feature development into clean branches, author standardized semantic commit messages, merge branches reliably, and resolve textual merge conflicts without losing critical logic.\n"
            "**Parent:** [[PRG-T00]] → [[PRG-T00-C03]] | **Prior Unit:** [[PRG-T00-C03-U03]] | **Next Unit:** [[PRG-T00-C03-U05]] | **Source:** [[R029]] (`Pro Git Book`)",
            id_map,
            color="blue_background",
        ),
        h2("1. Branching & Commit Graph Mental Model", id_map),
        num_item(
            "**Branches as Lightweight Pointers:** In Git, a branch is not a copy of directories; it is simply a 41-byte text file containing the SHA hash of its latest commit. Creating or switching branches is an instantaneous $O(1)$ operation.",
            id_map,
        ),
        num_item(
            "**Conventional Commits Standard:** Structured commit message format: `<type>(<optional scope>): <description>`:\n"
            "• `feat:` A new feature or capability for the user/system.\n"
            "• `fix:` A bug fix.\n"
            "• `refactor:` Code changes that neither fix a bug nor add a feature.\n"
            "• `test:` Adding missing tests or correcting existing tests.\n"
            "• `docs:` Documentation changes only.\n"
            "• `chore:` Build scripts, dependencies, or tool configurations.",
            id_map,
        ),
        num_item(
            "**Merge Mechanics (Fast-Forward vs 3-Way):** If the target branch has not diverged, Git moves the pointer forward (Fast-Forward). If both branches have advanced independently, Git calculates a 3-way merge between the common ancestor and the two tips, creating a merge commit.",
            id_map,
        ),
        divider_block(),
        h2("2. Branch Operations & Merge Conflict Resolution", id_map),
        code_block(
            "# 1. Create and switch to a feature branch\n"
            "git switch -c feat/billing-calculation\n"
            "\n"
            "# 2. Make atomic commits following Conventional Commits\n"
            "git commit -m \"feat(billing): add annual commitment discount logic\"\n"
            "git commit -m \"test(billing): verify family plan boundary conditions\"\n"
            "\n"
            "# 3. Merging back to main\n"
            "git switch main\n"
            "git merge feat/billing-calculation\n"
            "\n"
            "# 4. Resolving Conflicts (when branches diverge on same lines)\n"
            "# Git injects conflict markers into the affected files:\n"
            "# <<<<<<< HEAD\n"
            "# const taxRate = 0.08;\n"
            "# =======\n"
            "# const taxRate = account.isVatExempt ? 0 : 0.08;\n"
            "# >>>>>>> feat/billing-calculation\n"
            "\n"
            "# Manually edit the file to select the correct merged logic, then:\n"
            "git add src/billing.js\n"
            "git commit -m \"merge: resolve tax calculation conflict between main and feat/billing-calculation\"",
            "shell",
        ),
        divider_block(),
        h2("3. Complete Practice Guide", id_map),
        bullet("**Core Skills:** Creating and navigating branches (`git switch`), authoring conventional commits, executing merges, recognizing conflict markers, and verifying test suites pass after conflict resolution.", id_map),
        bullet("**Prior Units:** Builds directly upon the repository fundamentals in [[PRG-T00-C03-U03]].", id_map),
        bullet("**Common Traps:**", id_map, children=[
            bullet("Committing conflict marker lines (`<<<<<<<`, `=======`, `>>>>>>>`) directly to the repository without editing them out, resulting in syntax errors.", id_map),
            bullet("Resolving conflicts by unilaterally discarding a teammate's changes without understanding why they were introduced.", id_map),
            bullet("Developing directly on `main` instead of isolating experimental work on feature branches.", id_map),
        ]),
        bullet("**Cross-Subject Connections:** Directly mirrors the feature branch and code review workflows required in [[PRG-T00-C03-U05]] and future team engineering projects.", id_map),
        divider_block(),
        h2("4. Active Recall Questions", id_map),
        toggle_block(
            "Q1: When does Git perform a Fast-Forward merge, and how does it differ from a 3-Way Merge?",
            [p_block("A Fast-Forward merge occurs when there are no new commits on the base branch since the feature branch diverged. Git simply moves the base branch pointer forward to the tip of the feature branch without creating a new commit. A 3-Way merge occurs when both branches have diverged with independent commits; Git computes changes against their common ancestor and creates a new merge commit containing two parents.", id_map)],
            id_map,
        ),
        toggle_block(
            "Q2: What is the purpose of the Conventional Commits specification?",
            [p_block("It provides a standardized, machine-readable format that enables automated changelog generation, automatic semantic version bumping (SemVer), and crystal-clear commit log readability for code reviewers and continuous integration tools.", id_map)],
            id_map,
        ),
        toggle_block(
            "Q3: Why must you ALWAYS run test suites immediately after resolving a merge conflict?",
            [p_block("Resolving a merge conflict is manual surgery. Even if the code compiles and Git reports no syntax conflicts, the combined logic may violate runtime invariants or break assumptions made by either branch. Running tests verifies algorithmic and functional correctness before committing.", id_map)],
            id_map,
        ),
        divider_block(),
        h2("5. My Implementation & Mistake Log", id_map),
        todo_item("Create a feature branch, commit changes using `feat:` and `test:` prefixes, merge into main, and inspect the commit log graph with `git log --oneline --graph`.", id_map),
        todo_item("Simulate a merge conflict intentionally by modifying the same line on two branches, resolve it manually, and verify test passes.", id_map),
        quote_block("Document any merge conflicts, aborted merges (`git merge --abort`), or git rebase confusion encountered.", id_map),
    ]


def build_prg_t00_c03_u05(id_map):
    return [
        callout_block(
            "**Learning Objective:** Master collaborative GitHub and remote repository workflows: remote tracking branches (`origin`), `push`/`fetch`/`pull` mechanics, Pull Request (PR) lifecycle, automated CI status checks, and giving/receiving constructive code reviews.\n"
            "**Expected Output:** Push feature branches to remote repositories, open detailed pull requests with test evidence, interact with automated CI check runners, and conduct Senior Tech Lead code reviews.\n"
            "**Parent:** [[PRG-T00]] → [[PRG-T00-C03]] | **Prior Unit:** [[PRG-T00-C03-U04]] | **Next Unit:** [[PRG-T00-C03-U06]] | **Source:** [[R029]] (`Pro Git Book`)",
            id_map,
            color="blue_background",
        ),
        h2("1. Remote Repositories & Asynchronous Code Review Mental Model", id_map),
        num_item(
            "**Remote Tracking Branches:** A local repository tracks one or more remote endpoints (traditionally named `origin`). Remote tracking branches like `origin/main` represent the state of the remote repository at the time of the last `git fetch`.",
            id_map,
        ),
        num_item(
            "**Fetch vs Pull:** `git fetch` downloads objects and updates remote tracking references without touching your local working tree. `git pull` is shorthand for `git fetch` followed immediately by `git merge` into the current checked-out branch.",
            id_map,
        ),
        num_item(
            "**The Pull Request (PR) Contract:** A pull request is a formal proposal to merge a set of commits from a feature branch into a target branch. It serves as the discussion forum for design feedback, security review, performance validation, and automated Continuous Integration (CI) verification.",
            id_map,
        ),
        num_item(
            "**Senior Tech Lead Review Flow:** Professional code review examines code across 4 core vectors:\n"
            "1. Architectural Correctness & Invariant Enforcement\n"
            "2. Edge Case & Failure Boundary Resilience\n"
            "3. Cleanliness, Modularity & Anti-Pattern Elimination\n"
            "4. Comprehensive Test Suite Telemetry",
            id_map,
        ),
        divider_block(),
        h2("2. Remote Commands & PR Anatomy", id_map),
        code_block(
            "# 1. Link local repository to remote origin\n"
            "git remote add origin https://github.com/org/repo.git\n"
            "git remote -v\n"
            "\n"
            "# 2. Push feature branch and set upstream tracking\n"
            "git push -u origin feat/auth-tokens\n"
            "\n"
            "# 3. Sync updates from remote without clobbering local changes\n"
            "git fetch origin\n"
            "git status -uno    # Check if local branch is behind origin/main\n"
            "git merge origin/main",
            "shell",
        ),
        p_block(
            "Production PR Description Standard:\n"
            "• **Summary:** Concise explanation of what problem this PR solves.\n"
            "• **Key Architectural Changes:** Bullet points highlighting modified components and patterns.\n"
            "• **Test Evidence:** Exact telemetry showing automated tests passing (`npm test`).\n"
            "• **Breaking Changes / Migration Notes:** Notice of any schema, API, or config updates required.",
            id_map,
        ),
        divider_block(),
        h2("3. Complete Practice Guide", id_map),
        bullet("**Core Skills:** Configuring remotes, pushing tracking branches (`-u`), opening structured pull requests, interpreting CI pipeline statuses, and responding to code review comments with focused follow-up commits.", id_map),
        bullet("**Prior Units:** Combines branching from [[PRG-T00-C03-U04]] with automated scripts from [[PRG-T00-C03-U02]].", id_map),
        bullet("**Common Traps:**", id_map, children=[
            bullet("Using `git push --force` (`-f`) on shared collaboration branches, overwriting teammates' commits.", id_map),
            bullet("Opening massive 'kitchen-sink' pull requests with 2,000+ line diffs that are impossible to review effectively. Prefer small, atomic PRs under 400 lines.", id_map),
            bullet("Merging PRs while automated CI checks are failing or red.", id_map),
        ]),
        bullet("**Cross-Subject Connections:** Directly powers the AI Senior Tech Lead PR Review practice engine used in our workspace drills.", id_map),
        divider_block(),
        h2("4. Active Recall Questions", id_map),
        toggle_block(
            "Q1: Why should an engineer use `git fetch` followed by inspection instead of running `git pull` blindly?",
            [p_block("`git pull` automatically merges remote changes into the current branch. If upstream commits conflict or introduce breaking changes, an unexpected merge commit is created immediately. `git fetch` safely downloads remote objects, allowing the engineer to inspect the incoming diff (`git log HEAD..origin/main`) before deciding to merge or rebase.", id_map)],
            id_map,
        ),
        toggle_block(
            "Q2: What is the risk of using `git push --force` and what safer alternative exists?",
            [p_block("`git push --force` forcefully overwrites the remote branch reference, permanently erasing any commits pushed by other collaborators. A safer alternative is `git push --force-with-lease`, which only overwrites if the remote branch matches your local tracking reference, preventing accidental overwrite of others' work.", id_map)],
            id_map,
        ),
        toggle_block(
            "Q3: In a Senior Tech Lead code review, why is test telemetry considered mandatory in the PR description?",
            [p_block("Reviewers cannot execute every line of code mentally against all runtime edge cases. Test telemetry provides empirical proof that the author verified critical boundary conditions, zero regressions occurred, and all invariants hold.", id_map)],
            id_map,
        ),
        divider_block(),
        h2("5. My Implementation & Mistake Log", id_map),
        todo_item("Push a local branch to a remote GitHub repository and author a professional pull request with structured summary and test output.", id_map),
        todo_item("Review a simulated PR or drill submission as a Senior Tech Lead, identifying at least one edge case or architectural improvement.", id_map),
        quote_block("Document any remote authentication issues (SSH vs HTTPS tokens) or upstream tracking confusion.", id_map),
    ]


def build_prg_t00_c03_u06(id_map):
    return [
        callout_block(
            "**Learning Objective:** Master software documentation and issue tracking engineering: writing production-grade README specifications, minimal reproducible defect reports, feature proposals, and Architectural Decision Records (ADRs).\n"
            "**Expected Output:** Write clear, professional project documentation and actionable issue bug reports that allow any engineer to onboard, reproduce defects, or understand architectural decisions instantly.\n"
            "**Parent:** [[PRG-T00]] → [[PRG-T00-C03]] | **Prior Unit:** [[PRG-T00-C03-U05]] | **Source:** [[R029]] (`Pro Git Book`)",
            id_map,
            color="blue_background",
        ),
        h2("1. Documentation Architecture & Issue Lifecycle Mental Model", id_map),
        num_item(
            "**The README as the Front Door:** A repository without a README is unusable. The README provides immediate clarity on what problem the software solves, prerequisite dependencies, how to install and run it locally, and how to execute test suites.",
            id_map,
        ),
        num_item(
            "**Minimal Reproducible Bug Reports:** High-quality issue tracking eliminates ambiguity. A professional bug report includes the exact steps to reproduce, expected vs actual behavior, environment telemetry (Node version, OS), and a minimal code reproducer.",
            id_map,
        ),
        num_item(
            "**Architectural Decision Records (ADR):** Software systems degrade when architectural decisions are made in chat threads without lasting documentation. An ADR captures: Title, Status, Context, Decision, and Consequences.",
            id_map,
        ),
        divider_block(),
        h2("2. Production Documentation Standards", id_map),
        code_block(
            "# Project Name\n"
            "\n"
            "Brief 1-2 sentence description of the system and primary business value.\n"
            "\n"
            "## Prerequisites\n"
            "- Node.js >= 20.0.0\n"
            "- npm >= 10.0.0\n"
            "\n"
            "## Quickstart\n"
            "```bash\n"
            "git clone https://github.com/org/project.git\n"
            "cd project\n"
            "npm install\n"
            "npm test\n"
            "```\n"
            "\n"
            "## Architecture & Design Decisions\n"
            "- **State Architecture:** Immutable state containers with pure transition reducers.\n"
            "- **Error Handling:** Explicit Result types with zero unhandled Promise rejections.",
            "markdown",
        ),
        p_block(
            "Production Bug Report Specification:\n"
            "1. **Summary:** Clear, unambiguous title describing the defect.\n"
            "2. **Steps to Reproduce:** Numbered list starting from fresh clone.\n"
            "3. **Expected Behavior:** What the contract or specification dictates.\n"
            "4. **Actual Behavior:** What occurred (including full error stack trace).\n"
            "5. **Environment:** Node version, OS, browser, package lock hash.",
            id_map,
        ),
        divider_block(),
        h2("3. Complete Practice Guide", id_map),
        bullet("**Core Skills:** Writing clear markdown READMEs, structuring step-by-step bug reproduction issues, formatting stack traces into fenced code blocks, and authoring ADRs.", id_map),
        bullet("**Prior Units:** Complements all units in [[PRG-T00-C03]] by documenting the commands, scripts, and workflows established in U01 through U05.", id_map),
        bullet("**Common Traps:**", id_map, children=[
            bullet("Writing README setup instructions that work only on the author's local machine because global dependencies or hidden `.env` configurations are omitted.", id_map),
            bullet("Filing vague bug reports like 'the app crashed' without steps to reproduce or stack traces.", id_map),
            bullet("Documenting code changes without updating the corresponding README setup or usage documentation.", id_map),
        ]),
        bullet("**Cross-Subject Connections:** Directly prepares engineers for professional open-source contribution, team codebases, and technical documentation required in senior engineering roles.", id_map),
        divider_block(),
        h2("4. Active Recall Questions", id_map),
        toggle_block(
            "Q1: What are the essential sections every production README must contain?",
            [p_block("1. Project Title and Value Proposition, 2. Prerequisites (runtime versions, tools), 3. Installation & Quickstart commands, 4. Test Suite Execution instructions, 5. Architecture/Design overview, and 6. Contribution/License information.", id_map)],
            id_map,
        ),
        toggle_block(
            "Q2: Why is a Minimal Reproducible Example (MRE) critical when submitting a bug report?",
            [p_block("An MRE strips away all unrelated business logic, third-party libraries, and peripheral complexity, isolating the exact defect. This allows maintainers to reproduce and verify the bug immediately without guessing or wasting hours trying to recreate the environment.", id_map)],
            id_map,
        ),
        toggle_block(
            "Q3: What purpose does an Architectural Decision Record (ADR) serve in a growing codebase?",
            [p_block("An ADR records WHY a major technical decision was made (e.g. choosing SQLite over PostgreSQL, adopting strict TypeScript), what trade-offs were accepted, and what consequences follow. This prevents future team members from endlessly rehashing old debates or accidentally undoing intentional design trade-offs.", id_map)],
            id_map,
        ),
        divider_block(),
        h2("5. My Implementation & Mistake Log", id_map),
        todo_item("Draft a production-grade README for a local utility project including quickstart and test execution commands.", id_map),
        todo_item("Author a structured bug report issue for an edge case failure with exact reproduction steps and stack trace.", id_map),
        quote_block("Document any missing setup steps or ambiguous instructions identified during peer testing of your README.", id_map),
    ]
