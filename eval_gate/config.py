"""Gate thresholds for the eval run.

The gate is intentionally strict on wrong facts: a single critical failure
(a stated fact that is known-wrong) fails the whole run even if the pass
rate looks fine. That is the point of an eval gate -- a confident wrong
answer is worse than a hedged miss.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class GateConfig:
    min_pass_rate: float = 0.80       # fraction of cases that must pass
    max_critical_failures: int = 0    # allowed cases stating a wrong fact
    min_case_score: int = 4           # per-case pass bar, out of 6

    def evaluate(self, n_total: int, n_passed: int,
                 n_critical: int) -> dict:
        pass_rate = (n_passed / n_total) if n_total else 0.0
        reasons = []
        if pass_rate < self.min_pass_rate:
            reasons.append(
                f"pass rate {pass_rate:.2%} is below "
                f"threshold {self.min_pass_rate:.2%}")
        if n_critical > self.max_critical_failures:
            reasons.append(
                f"{n_critical} critical failure(s) exceeds allowed "
                f"{self.max_critical_failures}")
        return {
            "pass_rate": pass_rate,
            "passed": not reasons,
            "reasons": reasons,
        }
