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
  fails. The eval report is uploaded even for a failed gate. To prevent
  merging a failing PR, configure branch protection or a ruleset requiring
  this check; a workflow alone does not enforce merge blocking.

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
   from a model via an OpenAI-compatible endpoint). Opt-in and covered by
   mocked HTTP tests; live provider behavior has not been verified.

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
— but the machinery: break the stub in `eval_gate/catalog.py`, and the gate fails the way a real
regression gate should. `tests/test_gate.py::test_broken_answerer_fails_gate`
covers exactly that.

## Verification

- GitHub Actions runs the gate and uploads reports, including on failure.
- Tests cover LLM request shape, score validation and malformed response handling
  without credentials. Invalid scores fail closed instead of being coerced.
- Pass/fail Actions runs and both downloaded report artifacts were verified:
  [passing run](https://github.com/shazamlll/agent-eval-gate/actions/runs/43691837619),
  [negative control](https://github.com/shazamlll/agent-eval-gate/actions/runs/43691906295).
  The negative control scored 2/30 with 3 critical failures; it was reverted.
  The main branch had no branch protection at verification time, so these
  checks demonstrate failure detection, not enforced merge blocking.

## Model judge configuration

`python -m eval_gate.runner --judge llm` selects the implemented model adapter.
`OPENAI_API_KEY` selects OpenAI; with only `GEMINI_API_KEY`, the Gemini
OpenAI-compatible endpoint is selected. `LLM_BASE_URL` and `LLM_MODEL` override
defaults. Keep keys in the environment. The default deterministic run is offline.

## promptfoo port (demo supplement)

`promptfoo/` ports the first 5 cases to promptfoo (`promptfooconfig.yaml`,
offline: stub answerer + `contains`/`not-contains` assertions) plus an
`llm-rubric` variant (`promptfooconfig.llm.yaml`, needs `OPENAI_API_KEY`).
It demonstrates the OpenAI Evals -> promptfoo migration shape from the
official guide. Offline trial 2026-11-24: 5/5 pass, agrees 5/5 with the
local deterministic judge, $0 API cost. Details and honest limits in
`promptfoo/README.md`.

## Project layout

```
agent-eval-gate/
├── data/eval_set.json            # 30 synthetic retrieval QA cases
├── promptfoo/                    # promptfoo port (demo supplement)
│   ├── promptfooconfig.yaml      # offline: stub provider + deterministic assertions
│   ├── promptfooconfig.llm.yaml  # LLM-judge variant (needs OPENAI_API_KEY)
│   ├── stub_provider.py          # provider wrapping eval_gate.catalog.answer
│   └── results/                  # promptfoo run outputs
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
