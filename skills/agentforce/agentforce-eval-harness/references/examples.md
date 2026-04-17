# Examples — Agentforce Eval Harness

## Example 1: Regression detection on a prompt change

**Context:** Agent has 40 P0 fixtures with baseline scores. Engineer proposes a prompt change to make responses more concise.

**Problem:** Without a harness, "more concise" is subjective — regressions in correctness could sneak through.

**Solution:**

```
$ ./run_evals.py --agent customer-support-agent --baseline main

Running 40 P0 fixtures...

Baseline (main branch):
  correctness: 38/40 P0 passing (95%)
  grounding:   36/40 P0 passing (90%)
  tone:        39/40 P0 passing (97%)

Current (PR branch — 'make-concise' prompt change):
  correctness: 37/40 P0 passing (92%)  ← REGRESSION
  grounding:   38/40 P0 passing (95%)  ← improvement
  tone:        39/40 P0 passing (97%)  ← unchanged

Regressions:
  - return-flow-bulk-items: correctness 2→1
    Root cause: new concise prompt omitted guidance to confirm
    item IDs with the user before action.

PR BLOCKED. Fix the regression or update baseline with justification.
```

**Why it works:** Per-dimension scoring surfaces exactly which quality axis regressed. Engineer can iterate the prompt, rerun, and see the fix reflected.

---

## Example 2: LLM-as-judge calibration

**Context:** Team wants to scale from 30 human-judged fixtures to 200 LLM-judged fixtures.

**Problem:** LLM judges produce plausible-looking scores that don't match human judgment on edge cases.

**Solution:**

```
Step 1: Human scores 20 random fixtures (score, reason).
Step 2: LLM judge scores the same 20 fixtures.
Step 3: Compute agreement.

Dimension    Human   LLM     Agreement
correctness  avg 1.7 avg 1.8  18/20 = 90%  ✓
grounding    avg 1.5 avg 1.9  13/20 = 65%  ✗  RUBRIC TOO LOOSE
tone         avg 1.9 avg 1.9  19/20 = 95%  ✓

Action: tighten the grounding rubric. Specifically, the current rubric
says "2 = cited data from tool output" but doesn't require EXACT
quotation. LLM judge scores vague paraphrases as 2; humans score 1.

New rubric: "2 = cites verbatim or near-verbatim from tool output
(> 80% token overlap with tool output field). 1 = paraphrased or
mixed. 0 = not grounded in tool output."

Re-run agreement test: 17/20 = 85% — acceptable.
```

**Why it works:** Agreement measurement catches rubric drift before scaling. Tightening the rubric makes LLM judgment converge with human judgment.

---

## Example 3: Tool-call correctness test

**Context:** Agent's behavior is right, but it's calling the wrong tool under the hood — `Cancel_Subscription` instead of `Cancel_Order`.

**Problem:** Pure response-quality evals don't catch this. The response text is plausible; the side effect is wrong.

**Solution:**

```yaml
# fixture.md
expected_tool_calls:
  - turn: 2
    tool: Cancel_Order
    args:
      orderNumber: "A7842"
      reason: any
```

Harness captures the actual tool-call log per turn and diffs against expected. If agent calls `Cancel_Subscription` instead, the case fails before any response-quality scoring happens.

**Why it works:** Side-effect correctness is deterministic — no LLM judgment needed. Separating tool-call correctness from response-quality isolates root causes.

---

## Anti-Pattern: Single aggregate quality score

**What practitioners do:** Score an agent as "85% quality" or give it a single letter grade.

**What goes wrong:** A 95% correctness / 65% grounding / 95% tone agent scores the same aggregate as a 85%/85%/85% agent — but behaves very differently.

**Correct approach:** Track each dimension separately. Regressions on any P0 dimension block the PR.

---

## Anti-Pattern: Evals written after launch

**What practitioners do:** Ship the agent, then authors evals from user complaints.

**What goes wrong:** Every shipped regression costs user trust. Evals catch problems before users see them, not after.

**Correct approach:** Eval-driven development. Write P0 fixtures before the prompt is considered stable. Every prompt change must pass them.
