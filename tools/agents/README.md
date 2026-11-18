# Agent worker runner

`run-worker.sh` starts one Gemini (`agy`) job in a git worktree:

```bash
tools/agents/run-worker.sh <worktree> <branch> <prompt-file> <log-file>
```

- Stops the worker once its PR exists and the log has been quiet for `IDLE_AFTER_PR` seconds (default 300), or after `MAX_SECS` (default 7200).
- Tries the next model in `MODELS` only when the run failed for a quota / rate-limit reason — never after a kill, a timeout, or once a PR exists.
- Kills the worker's whole process group and any server started from the worktree when the job ends.
- Appends a rule to the prompt: stop every server you start; the final message ends the job.

Never chain workers with `agy ... || agy ...`: a killed first run starts a second worker on the same branch.
