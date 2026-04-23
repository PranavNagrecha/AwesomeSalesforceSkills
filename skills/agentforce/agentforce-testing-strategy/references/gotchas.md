# Agentforce Testing — Gotchas

## 1. Natural-Language Exact Match Is Brittle

Asserting "response contains 'Your refund was processed on…'" fails
every prompt-tuning round. Assert structure (topic, action, contains /
not-contains of stable tokens) instead.

## 2. Tone Drift Is Silent

A model update can keep routing correct but shift tone to the point of
brand mismatch. Periodic human review — not just asserts — catches this.

## 3. Flaky Goldens Discredit The Suite

If the suite flakes, the team stops trusting failures. Target <1%
flake. Rerun failures once; log rerun rate.

## 4. PII In Golden Set

Do not put real customer PII in test prompts. Use synthetic equivalents.

## 5. Action Unit Tests That Do Not Run The Action

Tests that only test the Apex class directly miss the invocation
contract. Also invoke via the Flow / Invocable path when that is how
the agent calls it.

## 6. "Regression" That Is Actually An Improvement

The model now answers a case better — but your golden's
`response_must_contain` was worded for the old response. Update the
golden after human review, don't revert.

## 7. Corpus Growth Without Pruning

Adding cases is easy; removing stale ones is ignored. Quarterly prune
protects signal.

## 8. No Dashboard, No Culture

If regression results live in CI logs, no one looks. A dashboard owned
by a named person is the minimum.
