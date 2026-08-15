# LLM Anti-Patterns — Agentforce Testing Strategy

---

## Anti-Pattern 1: Inventing a YAML test harness instead of using `AiEvaluationDefinition`

**What the LLM generates:** a clean, plausible YAML schema —

```yaml
tests:
  - id: gp-001
    prompt: "reset my password"
    expected:
      topic: account-self-service
      action: initiate_password_reset
      response_must_contain: ["verification"]
```

— plus a Python runner that calls the agent API and compares fields.

**Why it happens:** this is the shape of every LLM eval framework in the
model's training data (promptfoo, DeepEval, LangSmith, ragas). Agentforce's
native testing metadata is comparatively recent and thinly represented, so the
model reaches for the ecosystem-standard pattern and produces something that
looks right to anyone who has written evals elsewhere.

**Correct pattern:** Salesforce ships a real metadata type. `AiEvaluationDefinition`
holds `testCase` entries with `inputs.utterance` and `expectation` blocks; it
deploys with the agent, runs in Testing Center and via
`sf agent test run`, and is evaluated by the platform against the actual planner
([Testing API metadata
reference](https://developer.salesforce.com/docs/ai/agentforce/references/testing-api/testing-metadata-reference.html)).

**Detection hint:** the proposed harness has its own runner script and its own
schema. If nothing in the design deploys to the org, the tests are testing a
model of the agent rather than the agent.

---

## Anti-Pattern 2: Invented expectation names

**What the LLM generates:** `expected_topic`, `expected_action`, `must_contain`,
`must_not_contain`, `refuse: true`, `no_system_prompt_leak: true` — well-named,
internally consistent, and not real.

**Why it happens:** having (correctly) decided that expectations are the right
abstraction, the model names them the way an English-speaking engineer would.
The real names are less guessable than the concepts they encode.

**Correct pattern:** the documented `expectation.name` values are
`topic_sequence_match`, `action_sequence_match`, `bot_response_rating`,
`coherence`, `completeness`, `conciseness`, `output_latency_milliseconds`,
`string_comparison`, and `numeric_comparison`. The first three take an
`expectedValue`; the four quality checks take none. (`topic_sequence_match`
keeps the older word: *topic* was renamed *subagent* in April 2026 with no
change to functionality and no change to the API surface.)

**Detection hint:** any expectation name not on that list. Deploy the definition
to a scratch org before it reaches a design document — invented metadata fails
at deploy, which is a cheap way to find out.

---

## Anti-Pattern 3: `not_contains`, which does not exist

**What the LLM generates:**

```xml
<parameter><name>operator</name><value>not_contains</value></parameter>
```

for the zero-tolerance PII assertion — the most important assertion in the
suite.

**Why it happens:** every other comparison library has a negation, so its
absence is genuinely surprising and the model completes the symmetry.

**Correct pattern:** the operator set is `equals`, `contains`, `startswith`,
`endswith`, and four numeric comparisons. Express negatives by post-processing
`--result-format json` output. This is a better design regardless: the
forbidden-token list lives in one reviewable file and applies to every case,
rather than being scattered across the cases someone remembered to guard.

**Detection hint:** any negated operator, or an expectation that claims to prove
absence.

---

## Anti-Pattern 4: Exact-match assertions on generated prose

**What the LLM generates:**

```apex
Assert.areEqual('Your refund is pending.', response);
```

or a `string_comparison` with `operator = equals` against a full sentence.

**Why it happens:** the unit-testing instinct is overwhelming and correct
everywhere else. Deterministic assertion is what "test" means in the model's
strongest priors, and it has no representation of the response as a sample from
a distribution.

**Correct pattern:** exact on decisions (subagent, action sequence), `contains` on
a short invariant token, score on style. The test for whether an assertion
belongs: *if this fails, do I know something is broken?*

**Detection hint:** an expected value longer than a few words. Length correlates
almost perfectly with brittleness here.

---

## Anti-Pattern 5: Happy paths only, no adversarial suite

**What the LLM generates:** thorough coverage of the intended journeys — book a
room, check a balance, reset a password — and nothing that tries to break the
agent.

**Why it happens:** "write tests for this agent" reads as "cover the
functionality", and functionality is described by the subagents. Adversarial cases
require a threat model, which is not in the prompt and not derivable from the
agent's configuration.

**Correct pattern:** six categories, minimum: instruction override, PII echo,
off-scope, ambiguity, identity spoofing, and exfiltration via action. These are
the cases that produce incidents rather than bug reports, and they are the ones
that must run before every release.

**Detection hint:** zero test cases whose expected outcome is a refusal or an
empty `action_sequence_match`. An agent that never refuses anything in its test
suite has never been tested for refusal.

---

## Anti-Pattern 6: Real-looking PII in test utterances

**What the LLM generates:** `"My SSN is 123-45-6789"`, `"my email is
john.smith@gmail.com"`, `"card 4532 0151 1283 0366"` — plausible values because
plausibility makes a better example.

**Why it happens:** the model is optimising for realism in the example, and
realism is exactly wrong here. It has no representation of the test file's
distribution — git, every sandbox, every clone.

**Correct pattern:** reserved synthetic values only —`999-xx-xxxx` for SSN,
`4111 1111 1111 1111` (the universal test card), `example.com` for domains. Add
a pre-commit check over the definition files, because this leak is introduced by
the person building the safety net.

**Detection hint:** any identifier in a test utterance that would pass a
real-world format check *and* is not from a reserved range.

---

## Anti-Pattern 7: Assuming Apex coverage covers the action

**What the LLM generates:** a full `@IsTest` class per action, presented as
complete action coverage.

**Why it happens:** in every other Salesforce context it *is* complete. The
model's strong, correct prior about Apex testing does not account for a consumer
that selects the method by reading its description in natural language.

**Correct pattern:** the Apex test proves the implementation. It cannot prove
the action is assigned to a subagent, that the planner will select it, or that the
planner will fill its inputs correctly from an utterance — all of which are
determined by the `@InvocableMethod` and `@InvocableVariable` descriptions. Pair
every action with at least one `action_sequence_match` case.

**Detection hint:** the test plan has an Apex class per action and no evaluation
definition naming any of them.

---

## Anti-Pattern 8: Putting free-text quality scores in a blocking CI gate

**What the LLM generates:** a CI config that fails the build when
`coherence < 0.8`.

**Why it happens:** the score is a number, numbers have thresholds, thresholds
gate builds. It is the natural composition and it produces a gate that flakes on
day one.

**Correct pattern:** deterministic expectations gate; scored expectations trend.
Put `coherence`, `completeness`, `conciseness`, and latency on a dashboard with
an alert on sustained movement, not on a per-run threshold. A PR gate that
flakes is disabled within two sprints, taking the deterministic checks with it.

**Detection hint:** a hard threshold on any LLM-judged score in a blocking step.

---

## Anti-Pattern 9: Running the suite without `--wait`

**What the LLM generates:**

```bash
sf agent test run --api-name My_Suite --target-org ci
```

as a complete CI step.

**Why it happens:** it is the command from the documentation's first example,
and the async default is a detail one sentence further down.

**Correct pattern:** `--wait <minutes>` for any blocking use, plus
`--result-format junit|json` and `--output-dir` so the pipeline has an artefact.
Without `--wait` the command returns before the tests run and the build is green
on no evidence.

**Detection hint:** `sf agent test run` in a CI file with no `--wait`. This is
the single most common wiring bug in this domain and it fails *open*.

---

## Anti-Pattern 10: A one-shot suite with no maintenance loop

**What the LLM generates:** 200 goldens generated in one pass, delivered as the
finished testing strategy.

**Why it happens:** the request was "design a test suite" and a suite is a
static artefact in the model's frame. The operating loop — replay, triage,
prune — is process, not deliverable, and does not appear unless asked for.

**Correct pattern:** the suite is a living corpus. Weekly production replay
harvests real failures; quarterly pruning removes cases for retired behaviour;
triage of every nightly failure has three outcomes (revert, update the
expectation, add a case) and is never automated. A suite that only grows stops
being read; a suite that is never updated locks the agent to the behaviour of an
obsolete model.

**Detection hint:** the strategy has no named owner, no review cadence, and no
statement of what happens when a golden fails. Those three absences predict the
suite's abandonment more reliably than its case count predicts its quality.
