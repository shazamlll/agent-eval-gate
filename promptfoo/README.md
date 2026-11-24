# promptfoo port (demo supplement)

A promptfoo port of the same 5-case demo eval, kept here as a supplement to
the local eval gate -- not a replacement for it. It exists to show the
OpenAI Evals -> promptfoo migration shape from the official migration
guide: evals become a portable `promptfooconfig.yaml`, graders become
assertions, runs become `promptfoo eval` in CI.

## Files

- `promptfooconfig.yaml` -- offline config. Provider: `stub_provider.py`
  (the repo's own rule-based answerer, no API key). Assertions:
  `contains` for each gold fact, `not-contains` for each distractor --
  the deterministic equivalents of the rubric in `eval_gate/judge.py`.
- `promptfooconfig.llm.yaml` -- same 5 cases, same provider, but the judge
  is `llm-rubric` (the agent-eval-gate rubric: groundedness / relevance /
  accuracy 0-2, fail if accuracy < 2 or total < 4). Needs `OPENAI_API_KEY`.
- `stub_provider.py` -- promptfoo Python provider wrapping
  `eval_gate.catalog.answer`.
- `results/promptfoo-results-2026-11-24.json` -- output of the offline trial
  run (5/5 pass; see below).

## Run it

```bash
npx -y promptfoo@latest validate config -c promptfoo/promptfooconfig.yaml
npx -y promptfoo@latest eval -c promptfoo/promptfooconfig.yaml --no-cache \
  -o promptfoo/results/promptfoo-results-YYYY-MM-DD.json
npx -y promptfoo@latest view   # local results viewer
```

LLM-judge variant (needs a key):

```bash
export OPENAI_API_KEY=...
npx -y promptfoo@latest eval -c promptfoo/promptfooconfig.llm.yaml --no-cache
```

## Trial run 2026-11-24 (offline)

- Install (first `npx` download of promptfoo 0.126.0): ~80 s; cached
  afterwards (~4 s).
- `validate config`: ~5 s, "Configuration is valid."
- `eval --no-cache`: ~5 s, 5/5 passed (100%), 0 failed, 0 errors.
- Cross-check: the repo's own deterministic judge scores the same 5 stub
  answers 6/6 each, 5/5 pass, 0 critical -- promptfoo and the local judge
  agree 5/5. API cost: $0 (no model calls).
- Pitfalls (cosmetic): `telemetry.shutdown() timed out during shutdown`
  prints after validate/eval; exit code stays 0. The results table header
  shows the raw prompt template (`{{question}}` unrendered) -- display
  only, the provider receives the rendered prompt.

## Honest limits

- All data is synthetic (the same 30-case bookstore set); the scores have
  no reference value -- this is migration-shape demo material, not a
  benchmark.
- The `llm-rubric` config has NOT been run (no API key in this environment).
  Until it is, no claim is made about LLM-judge agreement with the
  deterministic judge.
- Score parity with OpenAI Evals cannot be tested here: there is no Evals
  export to compare against. The official guide's warning stands --
  similarity scores may differ across systems, and an LLM judge grader
  must be validated before it is used for regression decisions.
