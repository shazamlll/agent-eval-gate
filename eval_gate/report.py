"""Render eval results as a Markdown report and a JSON file."""

from __future__ import annotations

import json


def render_markdown(results: list[dict], gate: dict, config) -> str:
    n_total = len(results)
    n_passed = sum(1 for r in results if r["passed"])
    n_critical = sum(1 for r in results if r["critical"])
    status = "PASS" if gate["passed"] else "FAIL"

    lines = [
        "# Eval Report — Bookstore Retrieval QA",
        "",
        f"**Gate: {status}** — {n_passed}/{n_total} cases passed "
        f"({gate['pass_rate']:.1%}, threshold {config.min_pass_rate:.0%}), "
        f"{n_critical} critical failure(s) "
        f"(allowed {config.max_critical_failures}).",
        "",
    ]
    if not gate["passed"]:
        lines.append("## Why the gate failed")
        lines.append("")
        for reason in gate["reasons"]:
            lines.append(f"- {reason}")
        lines.append("")
    lines += [
        "## Cases",
        "",
        "| ID | Score | Result | Answer |",
        "|----|-------|--------|--------|",
    ]
    for r in results:
        verdict = "pass" if r["passed"] else "FAIL"
        if r["critical"]:
            verdict += " (critical: wrong fact)"
        answer = r["answer"].replace("|", "\\|").replace("\n", " ")
        lines.append(f"| {r['id']} | {r['total']}/6 | {verdict} | {answer} |")
    lines += [
        "",
        "## Rubric",
        "",
        "Each case is scored 0-2 on groundedness (gold facts present), "
        "relevance (answers the question), and accuracy (no known-wrong "
        "fact stated). A case passes at 4/6 or better with accuracy == 2.",
        "",
        "_Synthetic demo data only — all books, authors and answers are "
        "invented._",
        "",
    ]
    return "\n".join(lines)


def write_outputs(results: list[dict], gate: dict, config,
                  output_dir: str) -> tuple[str, str]:
    """Write report.md and results.json into output_dir. Returns both paths."""
    import os

    os.makedirs(output_dir, exist_ok=True)
    md_path = os.path.join(output_dir, "report.md")
    json_path = os.path.join(output_dir, "results.json")
    with open(md_path, "w", encoding="utf-8") as fh:
        fh.write(render_markdown(results, gate, config))
    payload = {
        "gate": gate,
        "thresholds": {
            "min_pass_rate": config.min_pass_rate,
            "max_critical_failures": config.max_critical_failures,
            "min_case_score": config.min_case_score,
        },
        "results": results,
    }
    with open(json_path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, ensure_ascii=False)
    return md_path, json_path
