---
name: agent-testing-and-evaluation
description: "Use when testing, evaluating, or building regression suites for Agentforce agents: conversation testing in Agent Builder, topic (now subagent) coverage and utterance testing, Testing API and AiEvaluationDefinition metadata, Agentforce DX CLI test runs (sf agent generate test-spec, sf agent test create/run/resume/results/list), evaluation metrics (containment rate, escalation rate, CSAT, topic activation accuracy), and post-deploy analytics via Enhanced Event Logs. Triggers: 'how do I test my Agentforce agent', 'agent routes to wrong topic', 'write utterance tests', 'regression test after topic change', 'measure agent quality', 'agent containment rate', 'run agent tests from the CLI'. NOT for agent creation, topic design, or action contract design — use agentforce/agentforce-agent-creation, agentforce/agent-topic-design, or agentforce/agent-actions respectively."
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
  - "run my Agentforce agent tests from the Salesforce CLI in a pipeline"
  - "generate a test spec YAML for Agentforce agent tests"
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
  - "test spec YAML scaffolded via sf agent generate test-spec for CLI-authored suites"
  - "topic coverage matrix showing utterances tested per topic"
  - "evaluation run results with pass/fail per test case and aggregate metrics"
  - "regression delta report identifying newly failing tests after a topic or action change"
  - "post-deploy monitoring recommendations using Enhanced Event Logs"
dependencies: []
version: 1.1.1
author: Pranav Nagrecha
updated: 2026-08-14
---

# Agent Testing and Evaluation

Use this skill when the work is validating that an Agentforce agent routes correctly, produces quality responses, and continues to behave as expected after configuration changes. This skill covers the full testing lifecycle: interactive conversation testing in Agent Builder, structured utterance and topic tests defined in `AiEvaluationDefinition` metadata, programmatic test execution via the Testing API (Connect API), evaluation metrics interpretation, and regression testing patterns across the DevOps lifecycle. It does not cover how to create an agent, design subagents, or build actions — those are covered by the sibling skills listed in Related Skills.

Agentforce testing sits at the intersection of deterministic validation (did the agent fire the right action?) and probabilistic quality assessment (did the response satisfy the customer?). Both dimensions matter. Ignoring either produces false confidence.

> **Terminology.** Agent *topics* were renamed *subagents* in April 2026. The
> change is vocabulary only — there are no changes to functionality, and the API
> surface did not rename. This skill therefore leads with *subagent* in prose but
> deliberately keeps *topic* everywhere the platform kept it: the
> `expectTopicName` and `actualTopicName` fields, the `topic_sequence_match`
> expectation, the "topic test" assertion category, the "topic activation
> accuracy" metric, and the search keywords readers still arrive with.

---

## Before Starting

Gather this context before working on anything in this domain:

- Is the agent in **Active** state? Testing API can test an Active agent in any org. The Conversation Preview panel in Agentforce Builder works on Draft agents too — use it during development.
- Which environment is being tested? Sandbox is the correct place for pre-production automated test suites. Data Cloud is generally not available in Developer Edition orgs by default; confirm Einstein is enabled and any Data Cloud grounding sources are seeded if tests depend on knowledge retrieval.
- What subagents exist and what are their classification descriptions? Utterance test design requires knowing the intended scope boundaries between subagents — ambiguous boundaries are the #1 source of routing failures.
- Do test cases need to invoke real external actions (callouts, record operations)? By default, test runs via the Testing API execute the agent's reasoning engine and subagent/action routing but do not submit DML or callouts to external systems. Plan mock data accordingly.
- Has a baseline evaluation run been captured? Regression testing requires a saved baseline. Capture one before any subagent, instruction, or action change.

---

## Core Concepts

### Agentforce Testing Center and AiEvaluationDefinition

Agentforce provides two testing surfaces that share the same underlying evaluation engine:

- **Testing Center UI** (Setup > Agentforce > Testing Center) — browser-based tool for creating, organizing, and running test suites against a named agent. Best for iterative development and ad-hoc validation.
- **Testing API** — programmatic interface combining `AiEvaluationDefinition` Metadata API types (for test definition) and Connect API endpoints (for test execution and result retrieval). Best for CI/CD pipeline integration and regression automation.

`AiEvaluationDefinition` is the canonical metadata type for a test suite. It defines the agent under test and a set of test cases. Each test case specifies:

| Field | Purpose |
|---|---|
| utterance | The user message sent to the agent |
| context variables | Optional session context (e.g., authenticated user, case ID) to simulate realistic scenarios |
| conversation history | Optional prior turns for multi-turn conversation tests |
| expectations | One or more assertions: expected subagent classification, expected action(s) invoked, instruction adherence score threshold, or response content criteria |

Test definitions deploy alongside the agent metadata, so test suites are version-controlled and environment-promotable.

### Agentforce DX CLI — the `sf agent test` Command Family

Agentforce DX adds a Salesforce CLI surface on top of the same `AiEvaluationDefinition` / Connect API machinery. For anyone wiring agent tests into a script or CI pipeline, these commands are the idiomatic path — raw curl against the Connect API (Pattern 1) still works but is no longer necessary:

| Command | Purpose |
|---|---|
| `sf agent generate test-spec` | Scaffold a **test spec YAML** — a local file listing the test cases for a specific agent. This is an authoring entry point that precedes any `AiEvaluationDefinition` metadata; the spec supports context variables and out-of-the-box metrics in the test output |
| `sf agent test create` | Take the test spec YAML and create the agent test (the `AiEvaluationDefinition`) in the dev org — and automatically sync the resulting metadata back into the local DX project source |
| `sf agent test run --api-name <name>` | Start a test run in the target org. **Asynchronous by default** — the command prints the `sf agent test resume` command to fetch results later. Add `--wait <minutes>` to block synchronously (the pipeline-gate mode) |
| `sf agent test resume` / `sf agent test results --job-id <id>` | Resume a previously started run / retrieve results of a completed run — the CLI equivalents of manually polling the Connect API job ID |
| `sf agent test list` | Enumerate the agent tests available in the target org (first column is the test API name) — useful for pipeline scripts that discover or validate test API names before invoking a run |
| `sf agent test run-eval` | Run rich evaluation tests against an agent — labeled **Beta** in the CLI command reference |

Two supporting notes:

- `sf agent test run` accepts `--result-format json|tap|junit` plus `--output-dir` to write result files to disk — JUnit output is what most CI systems parse natively for pass/fail gating.
- The generic `sf api request rest` command can call the same Connect API endpoints (including Get Test Results by `runId`) when you need an endpoint the `sf agent test` family doesn't wrap.

Deploying the `AiEvaluationDefinition` metadata itself remains a separate step via standard `sf project deploy start` — deployment installs the definition; only `sf agent test run` (or the Connect API POST) executes it.

### Three Test Types

The platform evaluates three distinct properties per test case:

1. **Topic test** — did the agent classify the utterance to the expected subagent? This is a deterministic pass/fail. A failing topic test means the classification descriptions need refinement or the utterance is ambiguous.
2. **Action test** — did the agent invoke the expected action or action sequence? Validates that the reasoning engine's plan matches design intent. Multi-step action sequences can be tested by specifying an ordered list.
3. **Instruction adherence test** — how well did the generated response follow the subagent's instructions? Evaluated by a secondary LLM judge on a pass/fail basis with configurable criteria. Useful for tone, constraint, and persona compliance checks.

You can combine all three expectations on a single test case or use them independently.

### Utterance Coverage

A subagent is not proven to work from a single utterance. Adequate coverage requires:

| Utterance class | Purpose |
|---|---|
| Happy path | Canonical utterances that clearly belong to the subagent |
| Edge-case utterances | Paraphrases, non-native English, abbreviations, typos |
| Boundary utterances | Phrasings near the edge of an adjacent subagent's scope; verify the agent picks the right subagent and not a neighbor |
| Out-of-scope utterances | Deliberately off-topic statements; verify the agent escalates or declines gracefully rather than hallucinating a subagent match |

A coverage matrix (subagent × utterance type) makes gaps visible. Without this, teams discover routing failures in production from real customer sessions.

### Evaluation Metrics

Post-deploy and ongoing quality measurement uses a set of standard operational metrics:

| Metric | What It Measures | Target Signal |
|---|---|---|
| **Topic activation accuracy** | % of test utterances routed to the correct subagent | > 90% for each subagent before go-live |
| **Containment rate** | % of sessions resolved by the agent without human escalation | Baseline varies by use case; declining rate signals subagent/action gaps |
| **Escalation rate** | % of sessions transferred to a human agent | Complement of containment; spikes indicate unexpected out-of-scope requests or agent failures |
| **Resolution rate** | % of sessions where the customer's issue was fully resolved | Higher bar than containment; a session can be contained but unresolved |
| **CSAT / satisfaction score** | Customer satisfaction collected at session end | Tracks perceived quality; lagging indicator but the ultimate measure |
| **Instruction adherence score** | % of responses scored as compliant by the LLM judge | Tracks response quality over time; regression here signals prompt drift |

No single metric is sufficient. Containment without CSAT can mask an agent that contains by frustrating customers. CSAT without containment rate masks a well-liked but expensive agent.

---

## Common Patterns

### Pattern 1: Pre-Launch Subagent Coverage Validation

**When to use:** Before activating a new agent or a significantly revised subagent set.

**How it works:**

1. Build a coverage matrix: list every subagent and define at least 5 utterances per subagent — 2 happy-path, 2 edge-case, 1 boundary utterance near an adjacent subagent.
2. Create one `AiEvaluationDefinition` file per subagent group (or one combined file). Each test case sets `expectTopicName` to the intended subagent.
3. Deploy the `AiEvaluationDefinition` to the sandbox via `sf project deploy start`.
4. Execute via the Testing API. Note the shape of these paths: the resource sits
   **directly** under `/services/data/vXX.0/einstein/` — there is no `connect/`
   segment — and every operation goes through the `/runs` collection. Detailed
   per-test-case output lives on a further `/results` sub-resource:

   | Operation | Method and path |
   |---|---|
   | Start a run | `POST /services/data/v63.0/einstein/ai-evaluations/runs` |
   | Poll status | `GET /services/data/v63.0/einstein/ai-evaluations/runs/{runId}` |
   | Retrieve results | `GET /services/data/v63.0/einstein/ai-evaluations/runs/{runId}/results` |


```bash
# Start the evaluation run
curl -X POST \
  https://ORG_DOMAIN.my.salesforce.com/services/data/v63.0/einstein/ai-evaluations/runs \
  -H "Authorization: Bearer SESSION_ID" \
  -H "Content-Type: application/json" \
  -d '{
    "aiEvaluationDefinitionName": "OrderAgentTopicTests"
  }'
# Response:
# {
#   "id": "0Xx000000000001AAA",
#   "status": "IN_PROGRESS",
#   "startTime": "2026-04-10T14:30:00.000Z"
# }
```

5. Poll the returned job ID until `status: Completed`:

```bash
curl https://ORG_DOMAIN.my.salesforce.com/services/data/v63.0/einstein/ai-evaluations/runs/0Xx000000000001AAA \
  -H "Authorization: Bearer SESSION_ID"
# Response when complete:
# {
#   "id": "0Xx000000000001AAA",
#   "status": "COMPLETED",
#   "summary": {
#     "totalTestCases": 12,
#     "passed": 10,
#     "failed": 2
#   },
#   "testCaseResults": [
#     {
#       "testCaseIndex": 0,
#       "utterance": "Where is my order?",
#       "expectations": { "expectTopicName": "OrderStatus" },
#       "actuals": { "actualTopicName": "OrderStatus" },
#       "result": "PASS"
#     },
#     {
#       "testCaseIndex": 3,
#       "utterance": "I was charged twice and want my money back",
#       "expectations": { "expectTopicName": "ReturnRequest" },
#       "actuals": { "actualTopicName": "BillingInquiry" },
#       "result": "FAIL"
#     }
#   ]
# }
```

6. Retrieve the per-test-case detail from the `/results` sub-resource. The status
   poll returns the run summary; it is `/results` that carries the full test-case
   report, so a pipeline that never calls it cannot explain *why* a run failed:

```bash
curl https://ORG_DOMAIN.my.salesforce.com/services/data/v63.0/einstein/ai-evaluations/runs/0Xx000000000001AAA/results \
  -H "Authorization: Bearer ACCESS_TOKEN"
```

6. Review results: any `FAIL` on a topic test means the utterance routed elsewhere. Inspect the `actualTopicName` in the result payload and tune the classification description of either the intended or the competing subagent.
7. Re-run until all topic tests pass. Document the final pass results as the baseline.

**Why not just use Conversation Preview manually:** Manual preview is valuable for exploratory testing but does not produce repeatable, trackable results. It cannot catch regressions after a future change.

**CLI alternative:** steps 4–5 (execute + poll) collapse into a single `sf agent test run --api-name OrderAgentTopicTests --wait 10` — see Pattern 4. The raw Connect API calls above remain useful when the calling system is not a Salesforce CLI environment.

### Pattern 2: Regression Suite After Subagent or Action Changes

**When to use:** Any time a subagent's classification description, instructions, or action set is modified.

**How it works:**

1. Before making changes, capture the current test run results as a baseline (save the JSON result payload from the Connect API or export from Testing Center).
2. Apply the subagent or action change in the sandbox.
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

### Pattern 4: CLI-Native Test Pipeline with Agentforce DX

**When to use:** Wiring agent tests into a CI/CD pipeline, or authoring tests from a DX project instead of hand-writing `AiEvaluationDefinition` XML.

**How it works:**

1. Scaffold the test spec YAML locally — the authoring precursor to any metadata:

```bash
sf agent generate test-spec
```

2. Create the test in the dev org from the spec. This creates the `AiEvaluationDefinition` in the org and automatically syncs the resulting metadata back into the DX project source, so the test is version-controlled without a manual retrieve:

```bash
sf agent test create   # pass the generated test spec YAML file
```

3. In the pipeline, run synchronously and emit CI-native output:

```bash
sf agent test run --api-name Order_Agent_Tests --target-org ci-sandbox \
  --wait 10 --result-format junit --output-dir ./agent-test-results
```

   `--wait <minutes>` blocks until completion so the pipeline step's exit status can gate promotion. `--result-format junit` (or `json` / `tap`) plus `--output-dir` writes result files most CI systems parse natively — no custom JSON-diffing script required for the pass/fail gate itself (you still persist the JSON payload for regression baselining, Pattern 2).

4. For long suites, run asynchronously instead: omit `--wait`, capture the printed `sf agent test resume` command, and fetch results in a later pipeline stage with `sf agent test resume` or `sf agent test results --job-id <id>`.
5. For scripts targeting multiple orgs, discover or validate test API names first with `sf agent test list` against the target org.

**Why not raw curl:** The Connect API calls in Pattern 1 work, but they require you to manage session tokens, polling loops, and result parsing yourself. The `sf agent test` family reuses the CLI's org auth, handles polling, and produces JUnit output for free. Keep curl (or `sf api request rest`) for endpoints the command family doesn't wrap.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Rapid iterative subagent tuning during development | Conversation Preview in Agentforce Builder | Fastest feedback loop; no deploy required for instruction changes |
| Pre-launch sign-off for a new agent | AiEvaluationDefinition + Testing API in sandbox | Produces structured pass/fail results and a saved baseline |
| Post-change regression check | Re-run existing test suite; diff against baseline | Catches regressions introduced by the change without manual re-testing |
| CI/CD pipeline gate | `sf agent test run --wait <min> --result-format junit --output-dir <dir>` | Synchronous exit status + JUnit files CI runners parse natively; raw Connect API curl is the fallback when the CLI is unavailable |
| Authoring tests without hand-writing AiEvaluationDefinition XML | `sf agent generate test-spec` then `sf agent test create` | Spec-YAML-first authoring; `test create` builds the org metadata and syncs it back to the DX project |
| Post-deploy production monitoring | Enhanced Event Logs + containment/escalation rate dashboards | Real conversation data; Testing API does not replace live monitoring |
| Evaluating response quality (tone, constraint adherence) | Instruction adherence tests in AiEvaluationDefinition | LLM-judge evaluation is more scalable than manual review at volume |
| Multi-turn conversation validation | conversationHistory field in AiEvaluationDefinition test case | Single-utterance tests cannot catch context-dependent failures |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on agent testing:

1. **Map subagent coverage** — list all subagents, identify utterance gaps, and produce a coverage matrix before writing any test cases. Prioritize boundary utterances between adjacent subagents.
2. **Author test cases** — either scaffold a test spec YAML with `sf agent generate test-spec` and create the org test (plus auto-synced metadata) with `sf agent test create`, or hand-author `AiEvaluationDefinition` metadata directly. Either way: structured test cases with utterances, expected subagent names, expected action sequences, and instruction adherence expectations. Include multi-turn conversation history for context-dependent flows.
3. **Deploy and execute in sandbox** — deploy the test definition via `sf project deploy start`, then execute with `sf agent test run --api-name <name> --wait <minutes>` (or the Testing API Connect endpoint `POST /connect/einstein/ai-evaluations` with manual polling when the CLI is not available).
4. **Review and iterate** — inspect `FAIL` results, identify whether the failure is in subagent routing (tune classification descriptions), action sequencing (revise subagent instructions or action order), or instruction adherence (tighten subagent instructions). Re-run until all cases pass.
5. **Capture baseline** — save the passing test run results as the regression baseline before any further changes.
6. **Integrate into DevOps pipeline** — add an `sf agent test run --wait <minutes> --result-format junit --output-dir <dir>` step to the promotion pipeline from sandbox to production and let the CI runner's JUnit parsing block promotion on test failures. Use `sf agent test list` in scripts that need to discover or validate test API names in the target org first.
7. **Monitor post-deploy** — track containment rate, escalation rate, and CSAT via Enhanced Event Logs reports. Treat anomalies as signals to add new test cases for the conversation patterns causing failures.

---

## Review Checklist

Run through these before marking testing work complete:

- [ ] Coverage matrix created: at least 5 utterances per subagent (happy path, edge case, boundary, out-of-scope).
- [ ] AiEvaluationDefinition metadata authored and version-controlled alongside agent metadata.
- [ ] All topic tests passing (100% correct topic activation across the test suite).
- [ ] Action sequence tests passing for all primary action flows.
- [ ] Instruction adherence tests included for subagents with strict tone or constraint requirements.
- [ ] Multi-turn conversation tests cover all context-dependent flows.
- [ ] Baseline test results saved before any subagent or action change.
- [ ] Regression diff reviewed after each change — no newly broken cases remain.
- [ ] Test execution integrated into the sandbox-to-production promotion pipeline (`sf agent test run --wait --result-format junit`, or Connect API when the CLI is unavailable).
- [ ] Enhanced Event Logs enabled on the production agent for post-deploy monitoring.
- [ ] Containment rate, escalation rate, and CSAT dashboards configured or scheduled.

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Test conversations do not invoke real DML or callouts** — Testing API evaluates the agent's reasoning and routing but action execution is simulated. Tests can pass 100% while a misconfigured action (wrong API endpoint, missing field mapping) fails only in a live session. Always run at least one live conversation test in sandbox with real data before promoting to production.
2. **AiEvaluationDefinition deploys but Testing API requires a separate execute call** — deploying the metadata does not run the tests. Teams sometimes deploy the definition and assume tests passed. You must explicitly `POST` to the Connect API execute endpoint and wait for the job to complete before checking results.
3. **Subagent classification is probabilistic — the same utterance can route differently on repeated runs** — the reasoning engine has inherent non-determinism. An utterance that sits on a subagent boundary may alternate between two subagents across test runs. Test suites with too many boundary utterances in the happy-path tier will produce flaky results. Move genuinely ambiguous utterances to a dedicated "boundary" tier and evaluate the routing distribution rather than expecting 100% consistency on them.
4. **Enhanced Event Logs only capture production conversations, not Testing API runs** — test results are returned in the Testing API response payload, not in Enhanced Event Logs. Teams expecting to find test run failures in the Event Log will find nothing. Use Event Logs only for post-deploy monitoring of real user sessions.
5. **Instruction adherence evaluation uses a secondary LLM judge and can be inconsistent at low test volumes** — the instruction adherence score is produced by a separate model evaluation, not a rule-based check. On very short or edge-case responses it can produce inconsistent pass/fail results across repeated runs of the same test. Use it as a trend signal, not a binary gate, until you have sufficient test volume to trust the distribution.
6. **`sf agent test run` is asynchronous by default — a CI step that omits `--wait` exits before any results exist** — without `--wait`, the command only prints the `sf agent test resume` command and returns immediately. A pipeline that greps that step's output for pass/fail will gate on nothing. Add `--wait <minutes>` for synchronous gating, or split into an async run stage plus a later `sf agent test results --job-id` stage.
7. **The VS Code Agent Tests panel requires the AiEvaluationDefinition in a local package directory** — tests run from VS Code execute in the same development org as `sf agent test run`, but VS Code additionally requires the test's `AiEvaluationDefinition` component to physically exist in a package directory of the DX project, not just in the org. `sf agent test create` satisfies this automatically because it syncs the metadata back; tests created only in the Testing Center UI won't appear until retrieved into source.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| `AiEvaluationDefinition` metadata file | Structured XML/JSON test definition for deployment and version control alongside agent metadata |
| Test spec YAML | CLI-authored list of test cases scaffolded with `sf agent generate test-spec`; input to `sf agent test create`, which builds the org test and syncs the metadata back to the DX project |
| Subagent coverage matrix | Spreadsheet or table mapping each subagent to its tested utterance types (happy path, edge case, boundary, out-of-scope) |
| Baseline test results | Saved Testing API result payload representing the last known-good agent state |
| Regression delta report | Diff between baseline and current test run identifying newly failing and newly passing cases |
| Post-deploy monitoring dashboard | Enhanced Event Logs–based report tracking containment rate, escalation rate, and CSAT over time |

---

## Related Skills

- `agentforce/agentforce-agent-creation` — use for standing up a new agent, channel assignment, and activation. Testing assumes the agent already exists.
- `agentforce/agent-topic-design` — use when subagent classification failures in tests indicate subagent boundary or description problems.
- `agentforce/agent-actions` — use when action sequence test failures indicate action configuration or contract issues.
- `devops/scratch-org-management` — use when the agent testing pipeline is part of a scratch org–based CI workflow.
