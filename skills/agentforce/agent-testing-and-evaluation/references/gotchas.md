# Gotchas — Agent Testing and Evaluation

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Test Conversations Do Not Execute Real Actions

**What happens:** Testing API evaluates whether the agent's reasoning engine selects the correct topic and action sequence, but it does not execute the actions against real data. DML operations, flow invocations, and external callouts are not triggered during a test run. A test case that expects `CreateCase` will pass if the reasoning engine plans to call `CreateCase` — regardless of whether the action's field mappings are valid or the callout endpoint is reachable.

**When it occurs:** Every time you rely solely on Testing API results to verify that an agent is production-ready for data-writing or integration-dependent flows.

**How to avoid:** Treat Testing API as a routing and reasoning validator, not a functional integration test. After the automated test suite passes, run at least one end-to-end live conversation in the sandbox with real test data to confirm that actions execute, DML succeeds, and callouts return expected responses before promoting to production.

---

## Gotcha 2: AiEvaluationDefinition Deployment Does Not Auto-Execute Tests

**What happens:** Teams deploy the `AiEvaluationDefinition` metadata type via Metadata API or `sf project deploy start` and assume the tests have been executed. The metadata deployment only installs the test definition into the org. Tests do not run until you explicitly call the Connect API execute endpoint (`POST /connect/einstein/ai-evaluations`).

**When it occurs:** In CI/CD pipelines where the deploy step and the test-execute step are not clearly separated. A pipeline that deploys and then immediately checks for test results will find no results because the test job has not been submitted.

**How to avoid:** Structure the pipeline as three explicit stages: (1) deploy agent metadata + AiEvaluationDefinition, (2) execute the test suite via Connect API, (3) poll the job ID for completion and parse results. Add a hard gate that fails the pipeline if any test case returns `FAIL`. Never infer test status from the deploy step.

---

## Gotcha 3: Topic Routing Is Probabilistic — Boundary Utterances Produce Flaky Tests

**What happens:** The Agentforce reasoning engine has inherent non-determinism. An utterance that sits on the semantic boundary between two topics may route to either topic on different invocations of the same test case. This causes test cases written for boundary utterances to produce intermittent failures ("flaky tests") that block pipeline runs without indicating a real regression.

**When it occurs:** When teams write test cases using phrasings that are intentionally close to a topic boundary — for example, "I was charged incorrectly and want a refund" which could plausibly map to either `BillingInquiry` or `ReturnRequest`. The test will sometimes pass and sometimes fail.

**How to avoid:** Separate the test suite into two tiers. Tier 1 contains deterministic assertions: clearly in-scope, unambiguous utterances that must always route correctly. Use these as pipeline gates. Tier 2 contains boundary and ambiguous utterances evaluated as distribution checks — run them a set number of times and assert that the correct topic wins the majority. Never use a single-run hard pass/fail gate on utterances you know are semantically ambiguous. The real fix is to refine classification descriptions until the boundary utterance consistently routes correctly, then promote it to Tier 1.

---

## Gotcha 4: Enhanced Event Logs Do Not Contain Testing API Run Data

**What happens:** Testing API runs are not surfaced in Enhanced Event Logs or in the standard conversation log objects (`ConversationEntry`, `MessagingSession`). Teams expect to debug a failing test case by looking it up in Event Logs and find nothing.

**When it occurs:** When the team's post-test investigation workflow assumes all conversation data appears in a single log. Testing API job results exist only in the Testing API job response payload (the JSON returned when polling the job ID). Once the job is discarded, detailed failure information may not be recoverable.

**How to avoid:** Always parse and persist the full Testing API result payload to a log file or artifact store as part of the CI pipeline. For debugging, retrieve the full result JSON from the completed job before the pipeline teardown step. Use Enhanced Event Logs exclusively for monitoring real user sessions after deploy.

---

## Gotcha 5: Instruction Adherence Tests Are Inconsistent at Low Volume

**What happens:** Instruction adherence expectations use a secondary LLM judge to evaluate the agent's response against the topic's instructions. This judge is itself a language model and does not produce identical scores on every invocation of the same test case. On short, terse, or edge-case responses, the adherence score can flip between pass and fail across repeated runs without any agent change.

**When it occurs:** Most often when instruction adherence tests are used as hard pipeline gates with a single-run pass/fail criterion, particularly for topics with complex or nuanced instruction sets.

**How to avoid:** Use instruction adherence tests as trend indicators rather than binary gates, especially early in the agent's testing lifecycle. Run them as informational checks alongside the deterministic topic and action tests. Once you have enough test-run history to understand the normal pass rate distribution for a given topic, you can set a threshold gate (e.g., "must pass > 80% of adherence checks over 5 runs") rather than relying on a single run. Reserve single-run hard gates for topic and action tests, which are deterministic.
