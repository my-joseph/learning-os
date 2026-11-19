# Agent worker runner

`run-worker.sh` starts one Gemini (`agy`) job in a git worktree:

```bash
tools/agents/run-worker.sh <worktree> <branch> <prompt-file> <log-file>
```

- Stops the worker once its PR exists and the log has been quiet for `IDLE_AFTER_PR` seconds (default 300), or after `MAX_SECS` (default 7200).
- Tries the next model in `MODELS` only when the run failed for a quota / rate-limit reason — never after a kill, a timeout, or once a PR exists.
- Kills the worker's whole process group and any server started from the worktree when the job ends.
- Default `MODELS="gemini-4-neon-high gemini-4-hydrogen-high gemini-4-argon-high"` (Neon primary after the 2026-11-19 A/B test; Hydrogen/Argon are quota fallbacks).
- Runs `agy --output-format stream-json`; after each model run it prints a `[usage] ...` line to the log and appends a JSON record (model, branch, outcome, input/output/thinking/cache/total tokens) to `USAGE_LOG` (default `<main checkout>/pilot/agent-usage.jsonl`, gitignored). Killed runs are counted from per-step usage (`tools/agents/usage_summary.py`).
- Read-only jobs: set `DONE_FILE=<report path>`; the job counts as done once that file is non-empty (same idle stop as a PR).
- Appends a rule to the prompt: stop every server you start; the final message ends the job.

Never chain workers with `agy ... || agy ...`: a killed first run starts a second worker on the same branch.
