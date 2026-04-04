# LLM Anti-Patterns — Agent Testing and Evaluation

Common mistakes AI coding assistants make when generating or advising on Agentforce agent testing and evaluation. These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Testing Only the Happy Path

**What the LLM generates:** A test suite where every test case is the most obvious, canonical utterance for the topic — "where is my order", "I want to return an item", "billing question" — with all cases passing.

**Why it happens:** LLMs pattern-match on the topic name or description and generate the most prototypical utterance. Training data bias toward simple, clear examples means edge cases, paraphrases, and boundary utterances are systematically omitted.

**Correct pattern:**

```
For each topic, test cases MUST include:
- 2 happy-path utterances (canonical, clearly in-scope)
- 2 edge-case utterances (paraphrase, typo, non-native phrasing, abbreviation)
- 1+ boundary utterances (semantically close to an adjacent topic's scope)
- 1+ out-of-scope utterances (deliberately off-topic to verify escalation or decline)
```

**Detection hint:** If every test case in a generated AiEvaluationDefinition has a different `expectTopicName` for each test case and none of them repeat the same topic with different utterances, the suite is almost certainly happy-path only.

---

## Anti-Pattern 2: Claiming the Testing API Executes Actions Against Real Data

**What the LLM generates:** Advice like "run the Testing API to verify that the CreateCase action creates a real case in the org" or "use the Testing API to confirm your callout endpoint is reachable."

**Why it happens:** LLMs conflate testing the reasoning/routing layer (what Testing API actually does) with integration testing of the actions themselves. The distinction between routing validation and functional execution is not prominent in training data.

**Correct pattern:**

```
Testing API validates:
  - Topic classification (did the agent route to the right topic?)
  - Action selection (did the reasoning engine plan to call the right action(s)?)
  - Instruction adherence (does the response text comply with topic instructions?)

Testing API does NOT:
  - Execute DML (no records are created/updated)
  - Invoke external callouts
  - Trigger Flows or Apex

For functional validation of action execution, run live sandbox conversations with real test data after the Testing API suite passes.
```

**Detection hint:** Any advice that includes phrases like "verify the action ran" or "confirm the record was created" in the context of Testing API results is the anti-pattern.

---

## Anti-Pattern 3: Ignoring Topic Boundary Overlap When Designing Tests

**What the LLM generates:** Test suites where each topic is tested independently, with no utterances that challenge the boundary between adjacent topics. Topics like `ReturnRequest` and `BillingInquiry` are tested in isolation with no utterances that could plausibly belong to either.

**Why it happens:** LLMs build test cases topic-by-topic, optimizing for coverage of the individual topic without modeling the competitive routing space. Real routing failures at topic boundaries are invisible in this approach.

**Correct pattern:**

```
For every pair of adjacent topics (topics with overlapping semantic territory):
- Identify 2-3 utterances that sit on the boundary (e.g., "I was charged twice and want a refund")
- Add these as test cases in BOTH topics' test sets
- For the primary intended topic, mark them as expected to route correctly
- Confirm they do NOT route to the wrong adjacent topic by adding a negative assertion
  or by reviewing actual routing in results
```

**Detection hint:** If two topics have semantically related classification descriptions and no shared boundary utterances appear in the test suite, the boundary overlap anti-pattern is in play.

---

## Anti-Pattern 4: Using Instruction Adherence Tests as Hard Pipeline Gates on the First Run

**What the LLM generates:** CI pipeline configuration that blocks promotion if any instruction adherence test case returns `FAIL`, treating instruction adherence with the same binary gate policy as topic and action tests.

**Why it happens:** LLMs generalize the "fail fast" CI principle uniformly across all test types without accounting for the LLM-judge variance in instruction adherence scoring.

**Correct pattern:**

```
Pipeline gate policy by test type:
  Topic tests:              Hard gate — must be 100% PASS before promotion
  Action sequence tests:    Hard gate — must be 100% PASS before promotion
  Instruction adherence:    Soft gate — run as informational, track trend over time
                            Only enforce a hard gate after establishing a stable
                            baseline pass rate distribution across multiple runs

Rationale: Instruction adherence uses an LLM judge that has inherent variance.
A single-run 100% gate will produce false-positive pipeline failures on valid agents.
```

**Detection hint:** If generated pipeline YAML or scripts treat all three test types with `if result != 100% PASS then fail`, and no distinction is made for instruction adherence, the anti-pattern is present.

---

## Anti-Pattern 5: Advising to Capture Test Results From Enhanced Event Logs

**What the LLM generates:** Advice to investigate failing test cases by looking them up in Enhanced Event Logs or `ConversationEntry` records, or recommendations to build dashboards off Testing API results using Event Log data.

**Why it happens:** Enhanced Event Logs is the correct place to find real user conversation data. LLMs overgeneralize this to all conversation-related data including Testing API runs, which do not write to Event Logs.

**Correct pattern:**

```
Data source   |  Use for
--------------|---------------------------------------------------------
Testing API   |  Test job results via Connect API job polling endpoint
              |  (persist the JSON payload to your artifact store)
Enhanced      |  Real user conversations after production deployment
Event Logs    |  Containment rate, escalation rate, CSAT trend monitoring
              |  NOT for testing API run investigation

To debug a failing test case:
  1. Parse the Testing API result payload (JSON from the job poll endpoint)
  2. Inspect actualTopicName, actualActions, and adherenceScore fields
  3. Do not look in Event Logs — the test run is not there
```

**Detection hint:** Any generated investigation steps that include phrases like "check the Enhanced Event Logs for the test run" or "find the test conversation in ConversationEntry" indicate this anti-pattern.

---

## Anti-Pattern 6: Treating a Passing Test Suite as Proof the Agent Is Production-Ready

**What the LLM generates:** A checklist or release process where "Testing API suite passes" is the final gate before production activation, with no further validation steps.

**Why it happens:** LLMs pattern-match software testing conventions where a passing test suite is a strong signal of readiness. For Agentforce agents, the test suite validates routing and reasoning but not action execution, real data access, channel surface behavior, or the full range of production utterance diversity.

**Correct pattern:**

```
Pre-production validation layers (all required):
  Layer 1: AiEvaluationDefinition test suite (routing + reasoning)
  Layer 2: Live sandbox conversation tests with real data (action execution)
  Layer 3: Channel surface smoke test (agent responds on the actual embedded deployment)
  Layer 4: Agent user permission validation (agent user can access required records)

Post-deploy validation:
  - Monitor containment rate + escalation rate for the first 48 hours
  - Review Enhanced Event Logs for unexpected topic activations or escalation spikes
  - Add new test cases for any failure patterns discovered in production
```

**Detection hint:** If a generated release checklist has `Testing API: all cases pass` as the last item before "activate in production," the anti-pattern is present.
