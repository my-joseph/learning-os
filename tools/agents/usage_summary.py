"""Sum agy stream-json / codex --json token usage from a worker log segment (stdin).

Prints one summary line and optionally appends a JSON record to a JSONL file.
Uses the final `result` event when present; otherwise sums per-step usage
(a killed run has no result event).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time

KEYS = ("input_tokens", "output_tokens", "thinking_tokens", "cache_read_tokens", "total_tokens")


def summarize(lines: list[str]) -> dict:
    steps = {k: 0 for k in KEYS}
    result: dict | None = None
    conversation = None
    for line in lines:
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if event.get("type") == "turn.completed" and isinstance(event.get("usage"), dict):
            # Codex CLI: one usage block per turn; input_tokens includes cached input.
            u = event["usage"]
            steps["input_tokens"] += int(u.get("input_tokens") or 0)
            steps["output_tokens"] += int(u.get("output_tokens") or 0)
            steps["thinking_tokens"] += int(u.get("reasoning_output_tokens") or 0)
            steps["cache_read_tokens"] += int(u.get("cached_input_tokens") or 0)
            steps["total_tokens"] += int(u.get("input_tokens") or 0) + int(u.get("output_tokens") or 0)
        elif event.get("type") == "thread.started":
            conversation = event.get("thread_id", conversation)
        elif event.get("event") == "result":
            result = event.get("result") or {}
            conversation = result.get("conversation_id", conversation)
        elif event.get("event") == "step_update":
            step = event.get("step_update") or {}
            conversation = step.get("conversation_id", conversation)
            usage = step.get("usage")
            if step.get("state") == "DONE" and isinstance(usage, dict):
                for k in KEYS:
                    steps[k] += int(usage.get(k) or 0)
    if result and isinstance(result.get("usage"), dict):
        usage = {k: int(result["usage"].get(k) or 0) for k in KEYS}
        source = "result"
    else:
        usage = steps
        source = "steps"
    return {
        "conversation_id": conversation,
        "status": (result or {}).get("status"),
        "duration_seconds": (result or {}).get("duration_seconds"),
        "source": source,
        **usage,
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--model", default="")
    ap.add_argument("--branch", default="")
    ap.add_argument("--outcome", default="")
    ap.add_argument("--append", default="", help="JSONL file to append the record to")
    args = ap.parse_args(argv)
    record = {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "model": args.model,
        "branch": args.branch,
        "outcome": args.outcome,
        **summarize(sys.stdin.read().splitlines()),
    }
    print(
        f"[usage] model={record['model']} total={record['total_tokens']} "
        f"in={record['input_tokens']} out={record['output_tokens']} "
        f"think={record['thinking_tokens']} cache={record['cache_read_tokens']} ({record['source']})"
    )
    if args.append:
        os.makedirs(os.path.dirname(os.path.abspath(args.append)), exist_ok=True)
        with open(args.append, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(record) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
