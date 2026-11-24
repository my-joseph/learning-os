#!/usr/bin/env bash
# Run one Gemini (agy) worker job in a git worktree, safely.
#
# Usage: tools/agents/run-worker.sh <worktree> <branch> <prompt-file> <log-file>
#
# Fixes two failure modes seen 2026-11-18:
#  1. A worker opens its PR and then sits idle forever ("waiting for 1 background task",
#     usually a `next start` it launched). The watchdog stops it once the PR exists and
#     the log has been quiet for IDLE_AFTER_PR seconds, plus a hard MAX_SECS limit.
#  2. `agy ... || agy --model <fallback>` started a second worker whenever the first was
#     killed. Here the fallback model runs ONLY when the first run failed for quota /
#     rate-limit reasons, never after a kill, a timeout, or once a PR exists.
#
# Env (optional): MODELS="gemini-4-neon-high gpt-6.2-sol gpt-6-luna",
#                 MAX_SECS=7200, IDLE_AFTER_PR=300, POLL=20,
#                 DONE_FILE=<report path for read-only jobs>,
#                 USAGE_LOG=<jsonl path; default <main checkout>/pilot/agent-usage.jsonl>
#
# Output is agy stream-json, so the log grows while the worker runs (idle detection) and
# every step carries token usage. After each model run the token totals are printed to the
# log and appended to USAGE_LOG, also when the run was killed.
set -u

if [ $# -ne 4 ]; then
  echo "usage: $0 <worktree> <branch> <prompt-file> <log-file>" >&2
  exit 2
fi
WT=$1
BRANCH=$2
PROMPT_FILE=$3
LOG=$4
# Neon first; GPT Luna (Codex pool) is the quota fallback. Hydrogen and Carbon share Neon's agy pool, so they are
# useless as fallbacks for Neon. Argon is retired. gpt-* models run through the Codex CLI, everything else through agy.
# A worker must never start another worker (nested dispatch burns quota and escapes review).
if [ "${LEARNINGOS_ROLE:-}" = "worker" ]; then
  echo "run-worker.sh: refusing to start a worker from inside a worker (LEARNINGOS_ROLE=worker)" >&2
  exit 64
fi
export LEARNINGOS_ROLE=worker
# Resolve the real agent CLIs now, then put shims first on PATH so the worker itself cannot
# start nested agents (it would otherwise call `agy`/`codex`/`claude` directly).
AGY_BIN=${AGY_BIN:-$(command -v agy || echo agy)}
SHIM_DIR=$(mktemp -d "${TMPDIR:-/tmp}/lo-worker-shims.XXXXXX")
for _cli in agy codex claude; do
  printf '#!/bin/sh\necho "%s is blocked inside a LearningOS worker (LEARNINGOS_ROLE=worker): workers never dispatch other agents" >&2\nexit 64\n' "$_cli" >"$SHIM_DIR/$_cli"
  chmod +x "$SHIM_DIR/$_cli"
done
MODELS=${MODELS:-"gemini-4-neon-high gpt-6.2-sol gpt-6-luna"}
CODEX_BIN=${CODEX_BIN:-/Applications/ChatGPT.app/Contents/Resources/codex-cli/bin/codex}
CODEX_EFFORT=${CODEX_EFFORT:-high}
MAX_SECS=${MAX_SECS:-7200}
IDLE_AFTER_PR=${IDLE_AFTER_PR:-300}
POLL=${POLL:-20}
DONE_FILE=${DONE_FILE:-}
SCRIPT_DIR=$(cd "$(dirname "$0")" && pwd)

CLEANUP_NOTE='

RUNNER RULES: Stop every server or background process you started before you finish (for example `pkill -f "next start -p <port>"`); never leave background tasks running. Your final message ends the job — do not wait for anything after opening the PR.'

log() { echo "[run-worker $(date +%H:%M:%S)] $*" >>"$LOG"; }

pr_exists() {
  gh pr list --head "$BRANCH" --state all --json number -q '.[0].number' 2>/dev/null | grep -q .
}

pr_head_oid() {
  gh pr list --head "$BRANCH" --state all --json number,headRefOid -q '.[0].headRefOid' 2>/dev/null
}

job_done() {
  if [ -n "$DONE_FILE" ]; then
    [ -s "$DONE_FILE" ]
    return
  fi
  if [ "$INITIAL_PR_EXISTS" -eq 0 ]; then
    pr_exists
    return
  fi
  pr_exists || return 1

  CURRENT_PR_HEAD=$(pr_head_oid)
  if [ -n "$INITIAL_PR_HEAD" ] && [ -n "$CURRENT_PR_HEAD" ]; then
    [ "$CURRENT_PR_HEAD" != "$INITIAL_PR_HEAD" ]
    return
  fi

  CURRENT_HEAD=$(git rev-parse HEAD 2>/dev/null) || return 1
  [ "$CURRENT_HEAD" != "$INITIAL_HEAD" ] || return 1
  [ "$(git rev-parse "origin/$BRANCH" 2>/dev/null)" = "$CURRENT_HEAD" ] || return 1
  git diff --quiet && git diff --cached --quiet
}

# Kill the worker and everything it spawned (it runs in its own process group).
stop_tree() {
  local pgid=$1
  kill -TERM -- "-$pgid" 2>/dev/null
  sleep 5
  kill -KILL -- "-$pgid" 2>/dev/null
}

# Servers started from this worktree (next start/dev, node test runners) die with the job.
stop_worktree_servers() {
  pkill -f "$WT/practice-studio/node_modules" 2>/dev/null
  pkill -f "$WT/node_modules" 2>/dev/null
}

file_size() { wc -c <"$LOG" 2>/dev/null | tr -d ' '; }

cd "$WT" || { echo "no worktree $WT" >&2; exit 2; }
if [ -z "${USAGE_LOG:-}" ]; then
  COMMON=$(git rev-parse --path-format=absolute --git-common-dir 2>/dev/null)
  USAGE_LOG="${COMMON:+$(dirname "$COMMON")/}pilot/agent-usage.jsonl"
fi

# Sum token usage of this run's log segment and record it (works for killed runs too).
record_usage() { # <model> <start-offset> <outcome>
  tail -c +"$(($2 + 1))" "$LOG" | python3 "$SCRIPT_DIR/usage_summary.py" \
    --model "$1" --branch "$BRANCH" --outcome "$3" --append "$USAGE_LOG" >>"$LOG" 2>&1
}
: >>"$LOG"
PROMPT="$(cat "$PROMPT_FILE")$CLEANUP_NOTE"

INITIAL_HEAD=$(git rev-parse HEAD)
INITIAL_PR_EXISTS=0
INITIAL_PR_HEAD=""
if [ -z "$DONE_FILE" ]; then
  INITIAL_PR=$(gh pr list --head "$BRANCH" --state all --json number,headRefOid 2>/dev/null || echo '[]')
  INITIAL_PR_EXISTS=$(printf '%s' "$INITIAL_PR" | python3 -c 'import json,sys; data=json.loads(sys.stdin.read() or "[]"); print(1 if data else 0)')
  if [ "$INITIAL_PR_EXISTS" -eq 1 ]; then
    INITIAL_PR_HEAD=$(printf '%s' "$INITIAL_PR" | python3 -c 'import json,sys; print(json.load(sys.stdin)[0].get("headRefOid") or "")')
  fi
fi

set -m # background jobs get their own process group, so stop_tree reaches children
for MODEL in $MODELS; do
  START_OFFSET=$(file_size)
  log "start model=$MODEL branch=$BRANCH"
  case "$MODEL" in
    gpt-*)
      PATH="$SHIM_DIR:$PATH" "$CODEX_BIN" exec --json -m "$MODEL" -c model_reasoning_effort="$CODEX_EFFORT" \
        --dangerously-bypass-approvals-and-sandbox -C "$WT" "$PROMPT" </dev/null >>"$LOG" 2>&1 &
      ;;
    *)
      PATH="$SHIM_DIR:$PATH" "$AGY_BIN" -p "$PROMPT" --model "$MODEL" --dangerously-skip-permissions --output-format stream-json >>"$LOG" 2>&1 &
      ;;
  esac
  PID=$!
  STARTED=$(date +%s)
  LAST_SIZE=$(file_size)
  LAST_CHANGE=$STARTED
  REASON=""

  while kill -0 "$PID" 2>/dev/null; do
    sleep "$POLL"
    NOW=$(date +%s)
    SIZE=$(file_size)
    if [ "$SIZE" != "$LAST_SIZE" ]; then
      LAST_SIZE=$SIZE
      LAST_CHANGE=$NOW
    fi
    if [ $((NOW - STARTED)) -ge "$MAX_SECS" ]; then
      REASON="timeout"
    elif job_done && [ $((NOW - LAST_CHANGE)) -ge "$IDLE_AFTER_PR" ]; then
      REASON="idle-after-pr"
    fi
    if [ -n "$REASON" ]; then
      log "stopping worker ($REASON)"
      stop_tree "$PID"
      break
    fi
  done
  wait "$PID" 2>/dev/null
  RC=$?
  stop_worktree_servers
  record_usage "$MODEL" "$START_OFFSET" "rc=$RC${REASON:+ $REASON}"

  if job_done; then
    if [ -n "$DONE_FILE" ]; then
      log "done: report written (rc=$RC${REASON:+, $REASON})"
    else
      log "done: PR exists (rc=$RC${REASON:+, $REASON})"
    fi
    exit 0
  fi
  artifact_label="PR"
  [ -n "$DONE_FILE" ] && artifact_label="report"
  if [ -n "$REASON" ]; then
    log "stopped ($REASON) without a $artifact_label; not starting a fallback model"
    exit 1
  fi
  if [ "$RC" -eq 0 ]; then
    if [ -z "$DONE_FILE" ] && [ "$INITIAL_PR_EXISTS" -eq 1 ]; then
      log "finished rc=0 without advancing the existing PR"
      exit 1
    fi
    log "finished rc=0 without a $artifact_label"
    exit 0
  fi
  # Fall back to the next model only for quota / rate-limit failures of THIS run.
  if [ "$RC" -eq 3 ] || tail -c +"$((START_OFFSET + 1))" "$LOG" | grep -qiE 'quota|rate.?limit|resource.?exhausted|too many requests|\b429\b|usage limit|limit (reached|exceeded)'; then
    log "model $MODEL hit a limit (rc=$RC); trying the next model"
    continue
  fi
  log "failed rc=$RC (not a quota error); not starting a fallback model"
  exit "$RC"
done
log "all models exhausted"
exit 1
