# agent-eval-gate

> **Portfolio demo, not production.** A small, self-contained example of how
> to put an LLM evaluation behind a CI gate: a rubric judge, pass thresholds,
> and a GitHub Actions check that fails the build when eval scores regress.
> All data is synthetic — every book, author, question and answer is invented.

## What it demonstrates

- **Rubric judge design** (`eval_gate/judge.py`): three dimensions —
  groundedness, relevance, accuracy — each scored 0–2, with the rubric
  written out in the code. A case passes at 4/6 with accuracy == 2.
- **Pass thresholds** (`eval_gate/config.py`): overall pass rate ≥ 80% and
  zero critical failures. A *critical* failure means the system stated a
  fact that is known-wrong — one of those fails the whole run even if the
  pass rate looks fine, because a confident wrong answer is worse than a
  hedged miss.
- **CI eval gate** (`.github/workflows/eval-gate.yml`): every pull request
  runs the tests and the eval; the runner exits non-zero when the gate
  fails, so a regression cannot be merged. The eval report is uploaded as
  an artifact.

## How it works

1. `data/eval_set.json` — 30 retrieval QA cases over a fictional online
   bookstore (question, gold facts that a good answer must state,
   distractors that a good answer must *not* state).
2. `eval_gate/catalog.py` — the synthetic catalog (12 invented books) and a
   tiny rule-based stub answerer. The stub exists so the gate has something
   deterministic to measure; it is not a QA system.
3. `eval_gate/judge.py` — the default judge. Deterministic and offline
   (keyword / fact-overlap matching), so CI runs with no API key.
4. `eval_gate/runner.py` — runs the eval, prints a summary, writes
   `runs/report.md` and `runs/results.json`, and exits 1 when the gate fails.
5. `eval_gate/llm_judge.py` — an LLM-as-judge adapter (same rubric, scores
   from a model via an OpenAI-compatible endpoint). **Not wired up** — see
   below.

## Run it locally

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m pytest -q            # unit tests
python -m eval_gate.runner    # run the eval gate (exit 0 = pass)
cat runs/report.md            # the Markdown eval report
```

Requires Python 3.11+. No API keys, no network access.

## Current results

On the stub answerer, the gate passes: 30/30 cases pass, 0 critical
failures (the exact numbers are in `runs/` after a local run). The
interesting part is not the score — the stub is deliberately easy to grade
— but the machinery: change a threshold in `eval_gate/config.py`, or break
the stub in `eval_gate/catalog.py`, and the gate fails the way a real
regression gate should. `tests/test_gate.py::test_broken_answerer_fails_gate`
covers exactly that.

## Remaining work

For a follow-up agent (deployment / wiring — intentionally not done here):

- [ ] Verify the Actions gate on a real PR: open a PR that lowers a score
      (e.g. break the stub answerer) and confirm the check goes red, then
      revert.
- [ ] Wire the LLM judge: pick a cheap model (e.g. a Gemini flash-tier
      model), set `GEMINI_API_KEY` or `OPENAI_API_KEY`, run
      `python -m eval_gate.runner --judge llm`, and compare its agreement
      with the deterministic judge on the same 30 cases. The prompt and
      response parsing in `eval_gate/llm_judge.py` have never been run
      against a live endpoint.
- [ ] Optional: add a second eval set (e.g. multi-turn questions) once the
      LLM judge is verified.

## Project layout

```
agent-eval-gate/
├── data/eval_set.json            # 30 synthetic retrieval QA cases
├── eval_gate/
│   ├── catalog.py                # synthetic catalog + stub answerer
│   ├── judge.py                  # deterministic rubric judge (default)
│   ├── llm_judge.py              # LLM judge adapter (disabled by default)
│   ├── config.py                 # gate thresholds
│   ├── report.py                 # Markdown + JSON report rendering
│   └── runner.py                 # CLI: run eval, exit 1 on gate failure
├── tests/                        # pytest: judge, gate, report
└── .github/workflows/eval-gate.yml
```

## License

MIT — see [LICENSE](LICENSE).
