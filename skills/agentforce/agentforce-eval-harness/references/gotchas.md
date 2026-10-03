# Gotchas: Agentforce Eval Harness

Non-obvious behaviours that cause production problems. Gotchas 11 to 17 are platform facts with a cited source. Gotchas 1 to 10 are harness-design lessons; each says where a platform source backs it and marks the rest UNVERIFIED.

## Gotcha 1: Non-determinism in LLM responses breaks exact-match assertions

**What happens:** A case passes once and fails on the next run. The agent's wording varies between runs.

**When it occurs:** Assertions that require an exact text match with the reference answer.

**How to avoid:** Score wording with a rubric or a semantic comparison. Keep exact matching for deterministic side effects: subagent name, action names, action arguments.

**Source:** Generative AI guide (Spring '26), Troubleshooting Agents: "LLMs are nondeterministic, so there's always some variation in responses." The platform's own outcome check, `bot_response_rating`, compares meaning rather than text: "Even if the text of the actual outcome differs from the expected outcome, the test can still pass if the core meaning is the same" (Use Test Results to Improve Your Agent).

---

## Gotcha 2: LLM judges are biased toward longer responses

**What happens:** The judge scores verbose responses higher than concise, correct ones.

**When it occurs:** The rubric does not reward brevity or penalize filler.

**How to avoid:** Add a rubric clause: "A shorter correct response scores higher than a long response that adds filler." Calibrate against human scores on a schedule.

**Source:** UNVERIFIED (2026-10-03): no Salesforce source states a length bias. The platform does ship a `conciseness` quality metric ("Shorter is better"), which you can run beside the harness judge as a cross-check (Use Test Results to Improve Your Agent).

---

## Gotcha 3: Baseline scores drift when the platform changes underneath you

**What happens:** Scores shift overnight with no change in your agent.

**When it occurs:** The testing service or the underlying model changes. UNVERIFIED (2026-10-03): the cadence of model refreshes is not documented.

**How to avoid:** Track the per-run score distribution. When absolute scores move beyond noise, re-baseline with sign-off instead of blocking every PR.

**Source:** Considerations for the Testing API: "Because of continuous improvements to the testing service, sometimes test results may change."

---

## Gotcha 4: The fixture set goes stale while users move on

**What happens:** Evals pass, but production sessions show requests no fixture covers.

**When it occurs:** The fixture set is frozen at launch.

**How to avoid:** Review production sessions on a schedule and add fixtures for new request clusters. Retire fixtures nobody asks any more.

**Source:** Agentforce Analytics, Utterance Analysis in the Generative AI guide: utterances are grouped into clusters and categories, and you can filter for requests handled by system topics to "determine when to create topics and actions to meet what users are requesting." Those unsupported-request clusters are the fixture backlog.

---

## Gotcha 5: Running evals in production pollutes production data

**What happens:** An eval run creates real records. Production data fills with test artefacts.

**When it occurs:** Evals run against a shared or production org.

**How to avoid:** Run evals in a dedicated sandbox. Change agents there too, and promote only after the full suite passes.

**Source:** Headless Example: Optimize an Agent by Analyzing Production Data: "You don't want to make agent changes in a production environment" and "Only promote the new agent version to production if the full suite passes, including any pre-existing regression test cases."

---

## Gotcha 6: Tool-call capture needs a data source you have turned on

**What happens:** Tool-call assertions cannot be verified because there is no record of which actions ran.

**When it occurs:** The harness tries to read tool calls from session traces that were never enabled.

**How to avoid:** Read tool calls from the test result instead. Testing API results expose `generatedData.invokedActions`, and `sf agent test run --verbose` prints the generated data. If you also read session traces, turn on Agentforce Session Tracing and Audit and Feedback first.

**Source:** Add Custom Evaluation Criteria to a Test Case (JSONPath over `$.generatedData.invokedActions`); Export Agentforce Session Tracing Data (Beta), which requires both settings.

---

## Gotcha 7: LLM-as-judge cost scales with fixture count, and so does platform cost

**What happens:** Two hundred fixtures across four dimensions, run daily, produce a large bill on both sides: your judge model and the agent's own usage.

**When it occurs:** No cost budget on the eval pipeline.

**How to avoid:** Tier runs: P0 cases on every PR, P1 daily, P2 weekly and sampled. Budget both the judge spend and the org's consumption.

**Source:** Considerations for the Testing API: test runs consume Einstein Requests "in either a production or sandbox environment" and possibly Data 360 credits. A sandbox is not free.

---

## Gotcha 8: Reference answers go stale when test data changes

**What happens:** A reference answer says "order A7842 placed March 3", but the test record now has another date.

**When it occurs:** Reference answers embed literal test-data values.

**How to avoid:** Use placeholders that the harness resolves from a test-data manifest, such as `{{testOrder.orderNumber}}`. Resolve them before you generate an `AiEvaluationDefinition`, because the metadata has no placeholder syntax.

**Source:** UNVERIFIED (2026-10-03): no Salesforce source covers harness placeholders. The AiEvaluationDefinition field list (Metadata API reference) has no templating field, which is why resolution must happen before generation.

---

## Gotcha 9: A fixture passes alone and fails in the suite

**What happens:** A fixture passes every solo run and fails intermittently inside a 40-case suite.

**When it occurs:** State bleeds between cases: session variables, records created by an earlier case, or cached data.

**How to avoid:** Start each case with a clean session and fresh data. Put prior turns in `conversationHistory` instead of relying on an earlier case to set up state.

**Source:** Build Tests in Metadata API: context variables "are only set at the beginning of an agent session", and conversation history is passed as input to give a case its own multi-turn context.

---

## Gotcha 10: Judging the LLM instead of the agent

**What happens:** Scores rise when the model improves even though the agent design is still wrong.

**When it occurs:** Fixtures test general reasoning instead of this agent's subagents, actions and refusals.

**How to avoid:** Every fixture should exercise the agent's own logic: which subagent, which action, which arguments, which refusal. Pair each case with `topic_sequence_match` and `action_sequence_match` so a better model cannot mask a routing defect.

**Source:** Use Test Results to Improve Your Agent: `topic_sequence_match` checks the subagent chosen and `action_sequence_match` checks the actions used, each with PASS or FAILED.

---

## Gotcha 11: Omitting `subjectVersion` tests whatever version is active today

**What happens:** The same definition produces a different baseline the day someone activates a new agent version.

**When it occurs:** The `AiEvaluationDefinition` has no `subjectVersion`.

**How to avoid:** Pin `subjectVersion` (for example `v3`) in regression definitions. Bump it in the same PR that promotes the new version.

**Source:** Metadata API Developer Guide, AiEvaluationDefinition: `subjectVersion` is "the agent version to test. If not provided, the latest active version is used by default."

---

## Gotcha 12: Exit code 1 from `sf agent test run` is not "an assertion failed"

**What happens:** A CI job treats exit code 1 as a regression and blocks a PR whose assertions all passed. Or it treats exit code 0 as success and lets real failures through.

**When it occurs:** The pipeline reads only the process exit code.

**How to avoid:** Parse the JSON result and gate on each `metricScore`. Use `--result-format json` (or `junit`) with `--output-dir`, and poll with `sf agent test resume --job-id` when you do not pass `--wait`.

**Source:** Troubleshoot Agentforce DX Issues: "exit code 1 means test cases had execution errors, not that assertions failed. Check the result output to distinguish the two."

---

## Gotcha 13: Definitions and runs have hard ceilings

**What happens:** A generated definition with 1,200 cases fails to deploy. A CI matrix that starts many runs at once queues or errors.

**When it occurs:** The harness writes every fixture into one definition, or fans out runs per PR.

**How to avoid:** Split definitions by subagent and keep each under 1,000 cases. Cap concurrent runs below 10 per org.

**Source:** Considerations for the Testing API: "You can have up to 10 IN-PROGRESS runs at any time" and "the maximum number of test cases is 1,000" per AiEvaluationDefinition.

---

## Gotcha 14: Custom evaluation parameters are short and case sensitive

**What happens:** A `string_comparison` against a long JSONPath fails validation, or an `equals` check fails because the agent wrote "a7842" instead of "A7842".

**When it occurs:** Tool-argument assertions are translated directly into custom evaluations.

**How to avoid:** Keep each parameter value at 100 characters or fewer; shorten the JSONPath filter. Use `contains` or normalize upstream when case does not matter.

**Source:** Add Custom Evaluation Criteria to a Test Case: "Each parameter field is limited to 100 characters" and "All string comparison operators are case sensitive."

---

## Gotcha 15: Context variables cannot change mid-session

**What happens:** A fixture tries to simulate "the user switches account halfway through" by changing a context variable on turn 3. The variable keeps its first value.

**When it occurs:** Multi-turn fixtures model state changes through context variables.

**How to avoid:** Model the change through conversation history and an action that sets a variable. Use a separate case for each starting context.

**Source:** Build Tests in Metadata API: "By default, context variables are immutable and are only set at the beginning of an agent session. The only context variable that is editable after a session begins is EndUserLanguage."

---

## Gotcha 16: Production transcripts copied into fixtures leak personal data into source control

**What happens:** A fixture file in Git contains a real customer's name, email and order history.

**When it occurs:** Failures found in production are pasted straight into the fixture set.

**How to avoid:** Generalize the failure condition and scrub or synthesize every value before it lands in a fixture. The checker in `scripts/` warns on email, phone and SSN patterns.

**Source:** Headless Example: Optimize an Agent by Analyzing Production Data: "Never copy raw production records or transcripts into a test case, even temporarily. Generalize the failure condition and scrub or synthesize any supporting data first."

---

## Gotcha 17: A test against an unpublished or inactive agent fails before it runs

**What happens:** `agent test create` says the agent does not exist, or CI tests fail even though they pass locally.

**When it occurs:** The pipeline creates or runs tests before it publishes and activates the agent version.

**How to avoid:** Order the pipeline: deploy actions, publish the agent, activate the version, deploy the definition, run.

**Source:** Troubleshoot Agentforce DX Issues: "You must publish the agent to your org before you can create a test against it" and "Some tests require the agent to be activated. Add an agent activate step before running tests in your CI script."
