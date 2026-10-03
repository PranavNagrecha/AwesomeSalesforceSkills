# LLM Anti-Patterns — Agentforce Eval Harness

Common mistakes AI coding assistants make when authoring evals.

## Anti-Pattern 1: Single-dimension scoring

**What the LLM generates:** Rubric with one "quality" score 0-5.

**Why it happens:** LLMs default to aggregated quality metrics.

**Correct pattern:** Separate correctness, grounding, tone, safety. Each scored independently.

**Detection hint:** Rubric with < 3 dimensions.

---

## Anti-Pattern 2: Happy-path-only fixtures

**What the LLM generates:** 10 fixtures, all successful completion of the task.

**Why it happens:** LLMs follow the "write the test after the code works" pattern.

**Correct pattern:** For every happy path, author: ambiguity, refusal, escalation, correction, tool-failure. 5:1 non-happy:happy ratio.

**Detection hint:** Fixture set where all cases end with "successfully completed".

---

## Anti-Pattern 3: Exact-match response assertions

**What the LLM generates:** `assert actual_response == reference_response`.

**Why it happens:** LLMs treat agent testing like traditional code testing.

**Correct pattern:** Rubric-based scoring. Exact-match only for deterministic side-effects (tool-call names + args).

**Detection hint:** Any eval using `==` or exact string comparison on agent natural-language responses.

---

## Anti-Pattern 4: Judge model is same as agent model

**What the LLM generates:** Both the agent and the judge use "the same LLM we have access to".

**Why it happens:** LLMs don't think about judge bias.

**Correct pattern:** Judge with a different model (or at minimum, a different prompt). Same-model judges correlate errors with agent errors.

**Detection hint:** Single LLM provider string appears in both agent config and judge config.

---

## Anti-Pattern 5: Rubric definitions without calibration data

**What the LLM generates:** "0 = bad, 1 = okay, 2 = good".

**Why it happens:** LLMs produce plausible-looking rubric scaffolding without operationalizing it.

**Correct pattern:** Each rubric level has a concrete example + an anti-example. Calibration: 20 fixtures human-scored; agreement measured; rubric tightened until agreement ≥ 80%.

**Detection hint:** Rubric levels are single adjectives without examples.

---

## Anti-Pattern 6: Running evals in production org

**What the LLM generates:** Eval harness that points at `prod` alias.

**Why it happens:** LLMs don't think about data pollution.

**Correct pattern:** Dedicated eval sandbox, refreshed nightly from a Partial Copy.

**Detection hint:** Test config with target alias == "prod" or missing environment check.

---

## Anti-Pattern 7: No teardown between fixtures

**What the LLM generates:** Sequential fixture run without session reset.

**Why it happens:** LLMs treat fixtures like unit tests, forgetting conversational state.

**Correct pattern:** Each fixture starts with a clean session, clean test data, clean session variables.

**Detection hint:** Fixture harness that calls fixtures in a loop without a reset step.

---

## Anti-Pattern 8: Reference answers with hard-coded record IDs

**What the LLM generates:** Reference answer mentions "Order 0016E00000XYZ123".

**Why it happens:** LLMs copy a specific test run's output as the reference.

**Correct pattern:** Placeholders that the harness substitutes from a test-data manifest: `{{testOrder.orderNumber}}`.

**Detection hint:** Reference answers containing Salesforce-style IDs or specific record-data values.

---

## Anti-Pattern 9: Infinite retry on judge disagreement

**What the LLM generates:** "If judge scores vary across runs, re-run until consistent."

**Why it happens:** LLMs treat noise as a bug to retry away.

**Correct pattern:** Run 3× and take majority; if still flaky, the rubric is ambiguous — rewrite it.

**Detection hint:** Judge-scoring loops without a retry cap.

---

## Anti-Pattern 10: Eval coverage proportional to LOC

**What the LLM generates:** Fixture count based on action count ("5 actions → 5 fixtures").

**Why it happens:** LLMs map eval coverage to code coverage.

**Correct pattern:** Fixture count based on user-intent coverage. One action may need 5 fixtures (happy, ambiguous, refused, escalated, corrected); one subagent (called a topic before April 2026) may need 15. Coverage is defined by intent, not code.

**Detection hint:** Fixture-to-action or fixture-to-subagent ratio of 1:1.

---

## Anti-Pattern 11: Generating an AiEvaluationDefinition with no subjectVersion

**What the LLM generates:** A regression definition that names the agent in `subjectName` and stops there.

**Why it happens:** The Metadata API sample is copied with its required fields only, and `subjectVersion` is optional.

**Correct pattern:** Pin `subjectVersion` in every regression definition. Without it the latest active version is tested, so the baseline changes whenever anyone activates a version. Bump the pinned version in the same PR that promotes the agent.

**Detection hint:** `scripts/check_agentforce_eval_harness.py` rule AIEVAL-004.

---

## Anti-Pattern 12: Treating `sf agent test run` exit code 1 as "tests failed"

**What the LLM generates:** A CI step such as `sf agent test run ... || exit 1` with no parsing of the result.

**Why it happens:** Assistants map the command onto unit-test runners, where a non-zero exit means an assertion failed.

**Correct pattern:** Write the result with `--result-format json` (or `junit`) and `--output-dir`, then gate on each case's `metricScore`. Exit code 1 means execution errors, which need a different response (fix the pipeline, not the agent).

**Detection hint:** A pipeline that never reads the JSON or JUnit output of the run.

---

## Anti-Pattern 13: Turning every rubric dimension into a `string_comparison`

**What the LLM generates:** Custom evaluations that compare whole responses with `equals`, or JSONPath expressions longer than 100 characters.

**Why it happens:** Custom evaluations look like the deterministic assertion the harness wants, so the assistant uses them for wording too.

**Correct pattern:** Use custom evaluations only for values the agent passes to or receives from an action. Keep each parameter at 100 characters or fewer and remember that string operators are case sensitive. Leave wording quality to `bot_response_rating` and the harness judge.

**Detection hint:** Rules AIEVAL-011 and AIEVAL-012 in the checker; any `string_comparison` whose `actual` parameter is not a JSONPath into `generatedData`.

---

## Anti-Pattern 14: Pasting a production transcript in as the fixture

**What the LLM generates:** A fixture whose input transcript is a real conversation, names and order numbers included.

**Why it happens:** Real transcripts are the best evidence of how users phrase things, so the assistant keeps them verbatim.

**Correct pattern:** Keep the phrasing pattern and replace every value with a synthesized one or a placeholder. The Agentforce Developer Guide says never to copy raw production records or transcripts into a test case, even temporarily.

**Detection hint:** Rules AIEVAL-019 and FIX-006 (email, phone or SSN patterns) and FIX-005 (record IDs).
