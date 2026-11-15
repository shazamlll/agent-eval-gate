"""Eval runner CLI.

Runs the synthetic bookstore eval set through the stub answerer, scores
every answer with the judge, applies the gate thresholds, and writes a
Markdown report + JSON results file.

Exit code is 0 when the gate passes, 1 when it fails -- that is what makes
the GitHub Actions check fail on a regression.

Usage:
    python -m eval_gate.runner [--output-dir runs] [--judge deterministic]
    python -m eval_gate.runner --judge llm   # needs OPENAI_API_KEY or
                                             # GEMINI_API_KEY; not wired up
"""

from __future__ import annotations

import argparse
import json
import os
import sys

from eval_gate import catalog, judge as judge_mod
from eval_gate.config import GateConfig
from eval_gate.report import write_outputs

DATASET_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                            "data", "eval_set.json")


def load_dataset(path: str = DATASET_PATH) -> list[dict]:
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)["cases"]


def run(judge_name: str = "deterministic") -> tuple[list[dict], dict, GateConfig]:
    cases = load_dataset()
    if judge_name == "llm":
        from eval_gate.llm_judge import LLMJudge
        scorer = LLMJudge()
        scorer_fn = scorer.score_case
    elif judge_name == "deterministic":
        scorer_fn = judge_mod.score_case
    else:
        raise ValueError(f"unknown judge: {judge_name!r}")

    results = []
    for case in cases:
        answer = catalog.answer(case["question"])
        result = scorer_fn(case, answer)
        result.setdefault("judge", f"deterministic")
        results.append(result)

    config = GateConfig()
    n_passed = sum(1 for r in results if r["passed"])
    n_critical = sum(1 for r in results if r["critical"])
    gate = config.evaluate(len(results), n_passed, n_critical)
    return results, gate, config


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", default="runs",
                        help="where to write report.md and results.json")
    parser.add_argument("--judge", default="deterministic",
                        choices=["deterministic", "llm"],
                        help="deterministic (default, offline) or llm")
    args = parser.parse_args(argv)

    try:
        results, gate, config = run(args.judge)
    except RuntimeError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    md_path, json_path = write_outputs(results, gate, config, args.output_dir)
    n_passed = sum(1 for r in results if r["passed"])
    n_critical = sum(1 for r in results if r["critical"])
    status = "PASS" if gate["passed"] else "FAIL"
    print(f"gate: {status} — {n_passed}/{len(results)} passed "
          f"({gate['pass_rate']:.1%}), {n_critical} critical failure(s)")
    for reason in gate["reasons"]:
        print(f"  - {reason}")
    print(f"report: {md_path}")
    print(f"results: {json_path}")
    return 0 if gate["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
