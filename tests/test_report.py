"""Tests for report generation."""

import json
import os

from eval_gate.config import GateConfig
from eval_gate.report import render_markdown, write_outputs
from eval_gate.runner import run


def test_render_markdown_pass_and_fail():
    results, gate, config = run()
    md = render_markdown(results, gate, config)
    assert "# Eval Report" in md
    assert "Gate: PASS" in md
    assert "| R01 |" in md
    assert "30 cases passed" in md or "passed" in md

    failing_gate = {"pass_rate": 0.5, "passed": False,
                    "reasons": ["pass rate 50.00% is below threshold 80.00%"]}
    md_fail = render_markdown(results, failing_gate, config)
    assert "Gate: FAIL" in md_fail
    assert "Why the gate failed" in md_fail


def test_write_outputs_creates_files(tmp_path):
    results, gate, config = run()
    out_dir = str(tmp_path / "runs")
    md_path, json_path = write_outputs(results, gate, config, out_dir)
    assert os.path.exists(md_path)
    assert os.path.exists(json_path)
    with open(json_path, encoding="utf-8") as fh:
        payload = json.load(fh)
    assert len(payload["results"]) == 30
    assert payload["gate"]["passed"] is True
    assert payload["thresholds"]["min_pass_rate"] == 0.80
