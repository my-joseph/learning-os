import json

from tools.agents.usage_summary import main, summarize


def _step(state, usage=None):
    s = {"conversation_id": "c1", "state": state, "step_type": "agent_response"}
    if usage:
        s["usage"] = usage
    return json.dumps({"event": "step_update", "step_update": s})


def test_prefers_result_event():
    lines = [
        _step("DONE", {"input_tokens": 5, "total_tokens": 5}),
        json.dumps(
            {
                "event": "result",
                "result": {
                    "conversation_id": "c1",
                    "status": "SUCCESS",
                    "usage": {"input_tokens": 9, "output_tokens": 1, "total_tokens": 10},
                },
            }
        ),
    ]
    rec = summarize(lines)
    assert rec["source"] == "result"
    assert rec["total_tokens"] == 10
    assert rec["status"] == "SUCCESS"


def test_killed_run_sums_done_steps_and_ignores_noise():
    lines = [
        "[run-worker 10:00:00] start model=m",
        _step("ACTIVE", {"total_tokens": 999}),
        _step("DONE", {"input_tokens": 3, "output_tokens": 2, "total_tokens": 5}),
        _step("DONE", {"input_tokens": 4, "cache_read_tokens": 7, "total_tokens": 4}),
        "{not json",
    ]
    rec = summarize(lines)
    assert rec["source"] == "steps"
    assert rec["total_tokens"] == 9
    assert rec["cache_read_tokens"] == 7
    assert rec["conversation_id"] == "c1"


def test_main_appends_jsonl(tmp_path, monkeypatch, capsys):
    out = tmp_path / "sub" / "usage.jsonl"
    monkeypatch.setattr("sys.stdin", __import__("io").StringIO(_step("DONE", {"total_tokens": 2})))
    assert main(["--model", "m", "--branch", "b", "--outcome", "rc=0", "--append", str(out)]) == 0
    rec = json.loads(out.read_text().strip())
    assert rec["model"] == "m" and rec["total_tokens"] == 2
    assert "[usage] model=m total=2" in capsys.readouterr().out


def test_codex_turn_usage():
    lines = [
        json.dumps({"type": "thread.started", "thread_id": "t1"}),
        json.dumps(
            {
                "type": "turn.completed",
                "usage": {
                    "input_tokens": 100,
                    "cached_input_tokens": 80,
                    "output_tokens": 7,
                    "reasoning_output_tokens": 3,
                },
            }
        ),
    ]
    rec = summarize(lines)
    assert rec["conversation_id"] == "t1"
    assert rec["total_tokens"] == 107
    assert rec["cache_read_tokens"] == 80 and rec["thinking_tokens"] == 3
