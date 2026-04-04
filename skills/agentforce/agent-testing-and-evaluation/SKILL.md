---
name: agent-testing-and-evaluation
description: "Use when testing, evaluating, or building regression suites for Agentforce agents: conversation testing in Agent Builder, topic coverage and utterance testing, Testing API and AiEvaluationDefinition metadata, evaluation metrics (containment rate, escalation rate, CSAT, topic activation accuracy), and post-deploy analytics via Enhanced Event Logs. Triggers: 'how do I test my Agentforce agent', 'agent routes to wrong topic', 'write utterance tests', 'regression test after topic change', 'measure agent quality', 'agent containment rate'. NOT for agent creation, topic design, or action contract design — use agentforce/agentforce-agent-creation, agentforce/agent-topic-design, or agentforce/agent-actions respectively."
category: agentforce
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Operational Excellence
triggers:
  - "how do I test my Agentforce agent before going live"
  - "agent is routing to the wrong topic for some customer messages"
  - "I need to write regression tests so topic changes don't break existing conversations"
  - "how do I measure agent quality — containment rate, escalation rate, CSAT"
  - "I want to automate agent testing in CI so every deploy is validated"
tags:
  - agentforce
  - agent-testing
  - testing-api
  - utterance-testing
  - topic-coverage
  - evaluation-metrics
  - regression-testing
  - conversation-testing
inputs:
  - "agent API name and the org (sandbox or production) where testing will occur"
  - "list of topics and their classification descriptions"
  - "representative utterances for each topic including edge cases and ambiguous phrasings"
  - "expected topic, expected action sequence, and expected response qualities for each test case"
  - "baseline test results from the previous known-good agent version (for regression testing)"
outputs:
  - "AiEvaluationDefinition metadata file with structured test cases"
  - "topic coverage matrix showing utterances tested per topic"
  - "evaluation run results with pass/fail per test case and aggregate metrics"
  - "regression delta report identifying newly failing tests after a topic or action change"
  - "post-deploy monitoring recommendations using Enhanced Event Logs"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-04
---

# Agent Testing and Evaluation

Use this skill when the work is validating that an Agentforce agent routes correctly, produces quality responses, and continues to behave as expected after configuration changes. This skill covers the full testing lifecycle: interactive conversation testing in Agent Builder, structured utterance and topic tests defined in `AiEvaluationDefinition` metadata, programmatic test execution via the Testing API (Connect API), evaluation metrics interpretation, and regression testing patterns across the DevOps lifecycle. It does not cover how to create an agent, design topics, or build actions — those are covered by the sibling skills listed in Related Skills.

Agentforce testing sits at the intersection of deterministic validation (did the agent fire the right action?) and probabilistic quality assessment (did the response satisfy the customer?). Both dimensions matter. Ignoring either produces false confidence.

---

## Before Starting

Gather this context before working on anything in this domain:

- Is the agent in **Active** state? Testing API can test an Active agent in any org. The Conversation Preview panel in Agentforce Builder works on Draft agents too — use it during development.
- Which environment is being tested? Sandbox is the correct place for pre-production automated test suites. Data Cloud is generally not available in Developer Edition orgs by default; confirm Einstein is enabled and any Data Cloud grounding sources are seeded if tests depend on knowledge retrieval.
- What topics exist and what are their classification descriptions? Utterance test design requires knowing the intended scope boundaries between topics — ambiguous boundaries are the #1 source of routing failures.
- Do test cases need to invoke real external actions (callouts, record operations)? By default, test runs via the Testing API execute the agent's reasoning engine and topic/action routing but do not submit DML or callouts to external systems. Plan mock data accordingly.
- Has a baseline evaluation run been captured? Regression testing requires a saved baseline. Capture one before any topic, instruction, or action change.

---

## Core Concepts

### Agentforce Testing Center and AiEvaluationDefinition

Agentforce provides two testing surfaces that share the same underlying evaluation engine:

- **Testing Center UI** (Setup > Agentforce > Testing Center) — browser-based tool for creating, organizing, and running test suites against a named agent. Best for iterative development and ad-hoc validation.
- **Testing API** — programmatic interface combining `AiEvaluationDefinition` Metadata API types (for test definition) and Connect API endpoints (for test execution and result retrieval). Best for CI/CD pipeline integration and regression automation.

`AiEvaluationDefinition` is the canonical metadata type for a test suite. It defines the agent under test and a set of test cases. Each test case specifies:
- **utterance** — the user message sent to the agent
- **context variables** — optional session context (e.g., authenticated user, case ID) to simulate realistic scenarios
- **conversation history** — optional prior turns for multi-turn conversation tests
- **expectations** — one or more assertions: expected topic classification, expected action(s) invoked, instruction adherence score threshold, or response content criteria

Test definitions deploy alongside the agent metadata, so test suites are version-controlled and environment-promotable.

### Three Test Types

The platform evaluates three distinct properties per test case:

1. **Topic test** — did the agent classify the utterance to the expected topic? This is a deterministic pass/fail. A failing topic test means the classification descriptions need refinement or the utterance is ambiguous.
2. **Action test** — did the agent invoke the expected action or action sequence? Validates that the reasoning engine's plan matches design intent. Multi-step action sequences can be tested by specifying an ordered list.
3. **Instruction adherence test** — how well did the generated response follow the topic's instructions? Evaluated by a secondary LLM judge on a pass/fail basis with configurable criteria. Useful for tone, constraint, and persona compliance checks.

You can combine all three expectations on a single test case or use them independently.

### Utterance Coverage

A topic is not proven to work from a single utterance. Adequate coverage requires:

- **Happy path** — canonical utterances that clearly belong to the topic
- **Edge-case utterances** — paraphrases, non-native English, abbreviations, typos
- **Boundary utterances** — phrasings that sit near the edge of an adjacent topic's scope, used to verify the agent picks the right topic and not a neighbor
- **Out-of-scope utterances** — deliberately off-topic statements to verify the agent escalates or declines gracefully rather than hallucinating a topic match

A coverage matrix (topic × utterance type) makes gaps visible. Without this, teams discover routing failures in production from real customer sessions.

### Evaluation Metrics

Post-deploy and ongoing quality measurement uses a set of standard operational metrics:

| Metric | What It Measures | Target Signal |
|---|---|---|
| **Topic activation accuracy** | % of test utterances routed to the correct topic | > 90% for each topic before go-live |
| **Containment rate** | % of sessions resolved by the agent without human escalation | Baseline varies by use case; declining rate signals topic/action gaps |
| **Escalation rate** | % of sessions transferred to a human agent | Complement of containment; spikes indicate unexpected out-of-scope requests or agent failures |
| **Resolution rate** | % of sessions where the customer's issue was fully resolved | Higher bar than containment; a session can be contained but unresolved |
| **CSAT / satisfaction score** | Customer satisfaction collected at session end | Tracks perceived quality; lagging indicator but the ultimate measure |
| **Instruction adherence score** | % of responses scored as compliant by the LLM judge | Tracks response quality over time; regression here signals prompt drift |

No single metric is sufficient. Containment without CSAT can mask an agent that contains by frustrating customers. CSAT without containment rate masks a well-liked but expensive agent.

---

## Common Patterns

### Pattern 1: Pre-Launch Topic Coverage Validation

**When to use:** Before activating a new agent or a significantly revised topic set.

**How it works:**

1. Build a coverage matrix: list every topic and define at least 5 utterances per topic — 2 happy-path, 2 edge-case, 1 boundary utterance near an adjacent topic.
2. Create one `AiEvaluationDefinition` file per topic group (or one combined file). Each test case sets `expectTopicName` to the intended topic.
3. Deploy the `AiEvaluationDefinition` to the sandbox via `sf project deploy start`.
4. Execute via Testing API Connect endpoint: `POST /connect/einstein/ai-evaluations`.
5. Poll the returned job ID until `status: Completed`.
6. Review results: any `FAIL` on a topic test means the utterance routed elsewhere. Inspect the `actualTopicName` in the result payload and tune the classification description of either the intended or the competing topic.
7. Re-run until all topic tests pass. Document the final pass results as the baseline.

**Why not just use Conversation Preview manually:** Manual preview is valuable for exploratory testing but does not produce repeatable, trackable results. It cannot catch regressions after a future change.

### Pattern 2: Regression Suite After Topic or Action Changes

**When to use:** Any time a topic's classification description, instructions, or action set is modified.

**How it works:**

1. Before making changes, capture the current test run results as a baseline (save the JSON result payload from the Connect API or export from Testing Center).
2. Apply the topic or action change in the sandbox.
3. Re-run the existing `AiEvaluationDefinition` test suite against the modified agent.
4. Diff the new results against the baseline: look for test cases that were previously `PASS` and are now `FAIL` (newly broken) and test cases that were previously `FAIL` and are now `PASS` (intentional improvements or coincidental fixes).
5. Investigate and resolve all newly broken cases before promoting the change.
6. Update the baseline after deliberate improvements are confirmed.

**Why not skip the baseline:** Without a baseline, you cannot distinguish a regression from a pre-existing bug. Teams that skip baselining end up unable to tell whether a failing test is caused by the current change or was always broken.

### Pattern 3: Multi-Turn Conversation Testing

**When to use:** When the agent handles conversations that require context from prior turns (e.g., "change my order" after the agent has already retrieved the order details, or disambiguation flows).

**How it works:**

1. Identify conversation flows that have meaningful context dependency — where the correct agent behavior in turn N depends on what happened in turn N-1 or earlier.
2. In `AiEvaluationDefinition`, include a `conversationHistory` array in the test case input. Each element in the array is a prior turn with `role` (user or agent) and `content`.
3. The agent evaluation engine replays the conversation including the provided history, then evaluates only the final user utterance against the expectations.
4. Write separate test cases for different conversational states to test the full flow matrix, not just the terminal turn.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Rapid iterative topic tuning during development | Conversation Preview in Agentforce Builder | Fastest feedback loop; no deploy required for instruction changes |
| Pre-launch sign-off for a new agent | AiEvaluationDefinition + Testing API in sandbox | Produces structured pass/fail results and a saved baseline |
| Post-change regression check | Re-run existing test suite; diff against baseline | Catches regressions introduced by the change without manual re-testing |
| CI/CD pipeline gate | Testing API Connect endpoint triggered by deployment script | Automatable; blocks promotion on test failure |
| Post-deploy production monitoring | Enhanced Event Logs + containment/escalation rate dashboards | Real conversation data; Testing API does not replace live monitoring |
| Evaluating response quality (tone, constraint adherence) | Instruction adherence tests in AiEvaluationDefinition | LLM-judge evaluation is more scalable than manual review at volume |
| Multi-turn conversation validation | conversationHistory field in AiEvaluationDefinition test case | Single-utterance tests cannot catch context-dependent failures |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on agent testing:

1. **Map topic coverage** — list all topics, identify utterance gaps, and produce a coverage matrix before writing any test cases. Prioritize boundary utterances between adjacent topics.
2. **Author AiEvaluationDefinition metadata** — create structured test cases with utterances, expected topic names, expected action sequences, and instruction adherence expectations. Include multi-turn conversation history for context-dependent flows.
3. **Deploy and execute in sandbox** — deploy the test definition via Metadata API, execute via the Testing API Connect endpoint (`POST /connect/einstein/ai-evaluations`), and poll for completion.
4. **Review and iterate** — inspect `FAIL` results, identify whether the failure is in topic routing (tune classification descriptions), action sequencing (revise topic instructions or action order), or instruction adherence (tighten topic instructions). Re-run until all cases pass.
5. **Capture baseline** — save the passing test run results as the regression baseline before any further changes.
6. **Integrate into DevOps pipeline** — include a Testing API execution step in the promotion pipeline from sandbox to production. Block promotion on test failures.
7. **Monitor post-deploy** — track containment rate, escalation rate, and CSAT via Enhanced Event Logs reports. Treat anomalies as signals to add new test cases for the conversation patterns causing failures.

---

## Review Checklist

Run through these before marking testing work complete:

- [ ] Coverage matrix created: at least 5 utterances per topic (happy path, edge case, boundary, out-of-scope).
- [ ] AiEvaluationDefinition metadata authored and version-controlled alongside agent metadata.
- [ ] All topic tests passing (100% correct topic activation across the test suite).
- [ ] Action sequence tests passing for all primary action flows.
- [ ] Instruction adherence tests included for topics with strict tone or constraint requirements.
- [ ] Multi-turn conversation tests cover all context-dependent flows.
- [ ] Baseline test results saved before any topic or action change.
- [ ] Regression diff reviewed after each change — no newly broken cases remain.
- [ ] Testing API execution integrated into the sandbox-to-production promotion pipeline.
- [ ] Enhanced Event Logs enabled on the production agent for post-deploy monitoring.
- [ ] Containment rate, escalation rate, and CSAT dashboards configured or scheduled.

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Test conversations do not invoke real DML or callouts** — Testing API evaluates the agent's reasoning and routing but action execution is simulated. Tests can pass 100% while a misconfigured action (wrong API endpoint, missing field mapping) fails only in a live session. Always run at least one live conversation test in sandbox with real data before promoting to production.
2. **AiEvaluationDefinition deploys but Testing API requires a separate execute call** — deploying the metadata does not run the tests. Teams sometimes deploy the definition and assume tests passed. You must explicitly `POST` to the Connect API execute endpoint and wait for the job to complete before checking results.
3. **Topic classification is probabilistic — the same utterance can route differently on repeated runs** — the reasoning engine has inherent non-determinism. An utterance that sits on a topic boundary may alternate between two topics across test runs. Test suites with too many boundary utterances in the happy-path tier will produce flaky results. Move genuinely ambiguous utterances to a dedicated "boundary" tier and evaluate the routing distribution rather than expecting 100% consistency on them.
4. **Enhanced Event Logs only capture production conversations, not Testing API runs** — test results are returned in the Testing API response payload, not in Enhanced Event Logs. Teams expecting to find test run failures in the Event Log will find nothing. Use Event Logs only for post-deploy monitoring of real user sessions.
5. **Instruction adherence evaluation uses a secondary LLM judge and can be inconsistent at low test volumes** — the instruction adherence score is produced by a separate model evaluation, not a rule-based check. On very short or edge-case responses it can produce inconsistent pass/fail results across repeated runs of the same test. Use it as a trend signal, not a binary gate, until you have sufficient test volume to trust the distribution.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| `AiEvaluationDefinition` metadata file | Structured XML/JSON test definition for deployment and version control alongside agent metadata |
| Topic coverage matrix | Spreadsheet or table mapping each topic to its tested utterance types (happy path, edge case, boundary, out-of-scope) |
| Baseline test results | Saved Testing API result payload representing the last known-good agent state |
| Regression delta report | Diff between baseline and current test run identifying newly failing and newly passing cases |
| Post-deploy monitoring dashboard | Enhanced Event Logs–based report tracking containment rate, escalation rate, and CSAT over time |

---

## Related Skills

- `agentforce/agentforce-agent-creation` — use for standing up a new agent, channel assignment, and activation. Testing assumes the agent already exists.
- `agentforce/agent-topic-design` — use when topic classification failures in tests indicate topic boundary or description problems.
- `agentforce/agent-actions` — use when action sequence test failures indicate action configuration or contract issues.
- `devops/scratch-org-management` — use when the agent testing pipeline is part of a scratch org–based CI workflow.
