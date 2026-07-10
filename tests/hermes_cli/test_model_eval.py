"""Tests for ``hermes model-eval`` (hermes_cli.model_eval).

Fully offline: httpx is exercised against ``httpx.MockTransport`` (no real
socket, no real local model server needed) for the grading/table-building
tests, and the CLI-level exit-code tests monkeypatch ``run_eval`` /
``resolve_target`` directly so they never touch the network at all.
"""

import json
from argparse import Namespace

import httpx
import pytest

import hermes_cli.model_eval as model_eval
from hermes_cli.model_eval import (
    ERROR,
    FAIL,
    MANUAL,
    PASS,
    TIMEOUT,
    EvalOutcome,
    _grade,
    render_table,
    resolve_target,
    run_eval,
)


# ---------------------------------------------------------------------------
# Deterministic grading
# ---------------------------------------------------------------------------

class TestGrade:
    def test_instr_pass_exact_ok(self):
        assert _grade("instr", "OK") == PASS

    def test_instr_pass_ignores_whitespace_case_and_period(self):
        assert _grade("instr", " ok.\n") == PASS

    def test_instr_fail_wrong_content(self):
        assert _grade("instr", "Okay, sure!") == FAIL

    def test_json_pass_exact(self):
        assert _grade("json", '{"a":1}') == PASS

    def test_json_pass_ignores_surrounding_whitespace(self):
        assert _grade("json", '  {"a": 1}  \n') == PASS

    def test_json_fail_wrong_value(self):
        assert _grade("json", '{"a":2}') == FAIL

    def test_arith_pass(self):
        assert _grade("arith", "The answer is 42.") == PASS

    def test_arith_fail(self):
        assert _grade("arith", "43") == FAIL

    def test_manual_always_manual(self):
        assert _grade("manual", "anything at all") == MANUAL


# ---------------------------------------------------------------------------
# run_eval against a mocked httpx transport
# ---------------------------------------------------------------------------

def _mock_client_factory(handler):
    def factory():
        return httpx.Client(base_url="http://test-local", transport=httpx.MockTransport(handler))
    return factory


def _all_correct_handler(request: httpx.Request) -> httpx.Response:
    body = json.loads(request.content)
    prompt = body["messages"][0]["content"]
    if prompt.startswith("Reply with exactly"):
        content = "OK"
    elif prompt.startswith("Return JSON"):
        content = '{"a":1}'
    elif "17 + 25" in prompt:
        content = "42"
    else:
        content = "some manual answer, ungraded"
    return httpx.Response(200, json={"choices": [{"message": {"content": content}}]})


def test_run_eval_grades_each_prompt_correctly():
    outcomes = run_eval(
        base_url="http://test-local",
        model_id="test-model",
        client_factory=_mock_client_factory(_all_correct_handler),
    )

    assert len(outcomes) == len(model_eval.PROMPTS)
    assert [o.check for o in outcomes] == ["instr", "json", "manual", "arith", "manual"]
    assert [o.result for o in outcomes] == [PASS, PASS, MANUAL, PASS, MANUAL]
    for o in outcomes:
        assert o.latency_s >= 0


def _wrong_instr_handler(request: httpx.Request) -> httpx.Response:
    body = json.loads(request.content)
    prompt = body["messages"][0]["content"]
    if prompt.startswith("Reply with exactly"):
        content = "Sure, OK!"  # wrong -- fails the exact-match check
    elif prompt.startswith("Return JSON"):
        content = '{"a":1}'
    elif "17 + 25" in prompt:
        content = "42"
    else:
        content = "manual"
    return httpx.Response(200, json={"choices": [{"message": {"content": content}}]})


def test_run_eval_reports_fail_for_wrong_answer():
    outcomes = run_eval(
        base_url="http://test-local",
        model_id="test-model",
        client_factory=_mock_client_factory(_wrong_instr_handler),
    )
    assert outcomes[0].result == FAIL


def _connect_error_handler(request: httpx.Request) -> httpx.Response:
    raise httpx.ConnectError("connection refused", request=request)


def test_run_eval_marks_unreachable_server_as_error_not_exception():
    """A fully down server must not raise -- every prompt becomes ERROR."""
    outcomes = run_eval(
        base_url="http://test-local",
        model_id="test-model",
        client_factory=_mock_client_factory(_connect_error_handler),
    )
    assert len(outcomes) == len(model_eval.PROMPTS)
    assert all(o.result == ERROR for o in outcomes)


def _timeout_handler(request: httpx.Request) -> httpx.Response:
    raise httpx.TimeoutException("timed out", request=request)


def test_run_eval_marks_timeout_distinctly():
    outcomes = run_eval(
        base_url="http://test-local",
        model_id="test-model",
        client_factory=_mock_client_factory(_timeout_handler),
    )
    assert all(o.result == TIMEOUT for o in outcomes)


def test_render_table_contains_header_rows_and_summary():
    outcomes = [
        EvalOutcome(1, "p1", "instr", PASS, 0.12, "OK"),
        EvalOutcome(2, "p2", "json", FAIL, 0.34, '{"a":2}'),
        EvalOutcome(3, "p3", "manual", MANUAL, 0.56, "Tokyo"),
    ]
    table = render_table(outcomes, label="llama:test-model")

    assert "RESULT" in table
    assert "PASS" in table
    assert "FAIL" in table
    assert "MANUAL" in table
    assert "llama:test-model" in table
    assert "Summary:" in table


# ---------------------------------------------------------------------------
# resolve_target
# ---------------------------------------------------------------------------

def test_resolve_target_ollama_bypasses_probe(monkeypatch):
    def _boom():
        raise AssertionError("must not probe llama-server when --ollama is given")

    monkeypatch.setattr(httpx, "Client", lambda *a, **k: _boom())

    base_url, model_id = resolve_target(ollama_model="llama3.1:8b")
    assert base_url == model_eval.DEFAULT_OLLAMA_URL
    assert model_id == "llama3.1:8b"


def test_resolve_target_llama_server_probe_failure_falls_back_to_local(monkeypatch):
    class _RaisingClient:
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def get(self, *a, **k):
            raise httpx.ConnectError("down")

    monkeypatch.setattr(httpx, "Client", lambda *a, **k: _RaisingClient())

    base_url, model_id = resolve_target()
    assert base_url == model_eval.DEFAULT_LLAMA_SERVER_URL
    assert model_id == "local"


# ---------------------------------------------------------------------------
# cmd_model_eval CLI-level exit codes
# ---------------------------------------------------------------------------

def _args(ollama=None, timeout=60.0):
    return Namespace(ollama=ollama, timeout=timeout)


def test_cmd_model_eval_exits_nonzero_when_endpoint_unreachable(monkeypatch, capsys):
    monkeypatch.setattr(model_eval, "resolve_target", lambda **k: ("http://down", "local"))
    monkeypatch.setattr(
        model_eval,
        "run_eval",
        lambda **k: [
            EvalOutcome(i, p.prompt, p.check, ERROR, 0.01, "<ConnectError>")
            for i, p in enumerate(model_eval.PROMPTS, start=1)
        ],
    )

    with pytest.raises(SystemExit) as exc_info:
        model_eval.cmd_model_eval(_args())

    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "unreachable" in captured.err
    assert "RESULT" in captured.out  # table still printed


def test_cmd_model_eval_exits_nonzero_on_any_fail(monkeypatch, capsys):
    monkeypatch.setattr(model_eval, "resolve_target", lambda **k: ("http://ok", "local"))

    def _outcomes(**k):
        results = [PASS, FAIL, MANUAL, PASS, MANUAL]
        return [
            EvalOutcome(i, p.prompt, p.check, r, 0.01, "x")
            for i, (p, r) in enumerate(zip(model_eval.PROMPTS, results), start=1)
        ]

    monkeypatch.setattr(model_eval, "run_eval", _outcomes)

    with pytest.raises(SystemExit) as exc_info:
        model_eval.cmd_model_eval(_args())

    assert exc_info.value.code == 1


def test_cmd_model_eval_exits_zero_when_all_pass_or_manual(monkeypatch, capsys):
    monkeypatch.setattr(model_eval, "resolve_target", lambda **k: ("http://ok", "local"))

    def _outcomes(**k):
        results = [PASS, PASS, MANUAL, PASS, MANUAL]
        return [
            EvalOutcome(i, p.prompt, p.check, r, 0.01, "x")
            for i, (p, r) in enumerate(zip(model_eval.PROMPTS, results), start=1)
        ]

    monkeypatch.setattr(model_eval, "run_eval", _outcomes)

    with pytest.raises(SystemExit) as exc_info:
        model_eval.cmd_model_eval(_args())

    assert exc_info.value.code == 0
    assert "Summary:" in capsys.readouterr().out


def test_cmd_model_eval_uses_ollama_target_when_flag_given(monkeypatch):
    captured = {}

    def _fake_resolve_target(*, ollama_model=None):
        captured["ollama_model"] = ollama_model
        return (model_eval.DEFAULT_OLLAMA_URL, ollama_model)

    monkeypatch.setattr(model_eval, "resolve_target", _fake_resolve_target)
    monkeypatch.setattr(
        model_eval,
        "run_eval",
        lambda **k: [
            EvalOutcome(i, p.prompt, p.check, MANUAL if p.check == "manual" else PASS, 0.01, "x")
            for i, p in enumerate(model_eval.PROMPTS, start=1)
        ],
    )

    with pytest.raises(SystemExit):
        model_eval.cmd_model_eval(_args(ollama="llama3.1:8b"))

    assert captured["ollama_model"] == "llama3.1:8b"
