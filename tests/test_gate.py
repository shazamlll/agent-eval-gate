"""Tests for the gate thresholds and the full eval run."""

from eval_gate import catalog
from eval_gate.config import GateConfig
from eval_gate.runner import load_dataset, run


def test_gate_pass_rate_threshold():
    config = GateConfig(min_pass_rate=0.80, max_critical_failures=0)
    assert config.evaluate(30, 27, 0)["passed"] is True
    assert config.evaluate(30, 23, 0)["passed"] is False  # 76.7% < 80%


def test_gate_zero_critical_failures_allowed():
    config = GateConfig(min_pass_rate=0.80, max_critical_failures=0)
    result = config.evaluate(30, 30, 1)
    assert result["passed"] is False
    assert any("critical" in r for r in result["reasons"])


def test_gate_reasons_empty_on_pass():
    config = GateConfig()
    assert config.evaluate(10, 10, 0)["reasons"] == []


def test_full_run_passes_gate():
    """The stub answerer is good enough that the gate passes on main.

    If this fails, either the stub regressed or a dataset case changed --
    that is exactly what the CI gate is for.
    """
    results, gate, _config = run()
    assert len(results) == 30
    assert gate["passed"] is True, gate["reasons"]
    assert gate["pass_rate"] >= 0.80


def test_full_run_no_critical_failures():
    results, _gate, _config = run()
    critical = [r for r in results if r["critical"]]
    assert critical == []


def test_broken_answerer_fails_gate():
    """A deliberately bad answerer must trip the gate (proves the gate bites)."""
    from eval_gate import judge

    cases = load_dataset()
    wrong = "I don't know. Everything is in stock and costs $99.99."
    results = [judge.score_case(c, wrong) for c in cases]
    config = GateConfig()
    n_passed = sum(1 for r in results if r["passed"])
    n_critical = sum(1 for r in results if r["critical"])
    gate = config.evaluate(len(results), n_passed, n_critical)
    assert gate["passed"] is False
    assert n_critical > 0


def test_stub_answerer_covers_dataset():
    cases = load_dataset()
    for case in cases:
        answer = catalog.answer(case["question"])
        assert answer, f"empty answer for {case['id']}"
        assert "couldn't find an answer" not in answer, case["id"]
