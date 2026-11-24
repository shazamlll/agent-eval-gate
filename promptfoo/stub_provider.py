"""promptfoo provider: the repo's own rule-based stub answerer.

No API key, no network. promptfoo calls call_api(prompt, ...) with the
rendered prompt; this extracts the question line and answers it with
eval_gate.catalog.answer -- the same "system under test" the deterministic
judge in eval_gate/judge.py grades. That makes the promptfoo run a
like-for-like port of the local eval gate, not a new system.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from eval_gate.catalog import answer  # noqa: E402


def call_api(prompt: str, options: dict, context: dict) -> dict:
    match = re.search(r"Question: ([^\n]+)", prompt)
    question = match.group(1).strip() if match else prompt.strip()
    return {"output": answer(question)}
