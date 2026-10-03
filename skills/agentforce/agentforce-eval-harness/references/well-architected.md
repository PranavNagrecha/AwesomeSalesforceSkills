# Well-Architected Notes — Agentforce Eval Harness

## Relevant Pillars

- **Reliability** — Agents regress silently without evals. The harness is the structural safeguard that ensures prompt/tool changes don't break previously-working behavior. Every P0 case is a regression test.
- **Operational Excellence** — Treating prompts and tool descriptions as versioned code requires a gate equivalent to Apex unit tests. The harness provides that gate, integrated into CI, diff-based, blocks on regression.

## Architectural Tradeoffs

### Human vs LLM judging

| Approach | Pro | Con |
|---|---|---|
| Human judges | High quality, context-aware | Doesn't scale past ~30 fixtures per cycle |
| LLM-as-judge | Scales to hundreds | Requires calibration; biased toward verbosity; rubric must be tight |
| Rule-based checks | Deterministic | Only works for structural assertions (tool calls, schema) |

Recommended hybrid: rule-based for tool-call correctness, LLM-as-judge for response quality, human spot-check 10% of LLM judgments to catch calibration drift.

### Fixture coverage breadth vs depth

Breadth: many fixtures covering many subagents (called topics before April 2026).
Depth: fewer fixtures with richer multi-turn transcripts.

Rule: start broad (1-2 P0 fixtures per subagent) for launch coverage; deepen over time as production transcripts reveal ambiguity patterns.

### Baseline stability vs model refreshes

When Salesforce refreshes the underlying LLM:
- Absolute scores shift ±2-5% uniformly.
- Relative scores (PR-branch vs baseline) stay meaningful.
- Re-baseline quarterly or on confirmed model version changes.

## Anti-Patterns

1. **Launch-without-evals** — Shipping the agent, then writing evals from user complaints. Every regression costs user trust. Fix: eval-driven development; P0 fixtures before prompt stability.

2. **Single aggregate quality score** — One "85% quality" number hides dimension-specific regressions. Fix: per-dimension scoring, per-dimension PR gate.

3. **Happy-path-only fixtures** — Evals that only test successful completion miss every failure mode. Fix: 5:1 non-happy to happy case ratio.

4. **Unbounded LLM-judge spend** — Running 200 fixtures × 4 dimensions × daily burns budget fast. Fix: tier by severity; P0 on every PR, P2 weekly-sampled.

5. **Fixture set frozen after launch** — Evals pass, users fail. Fix: monthly review of production transcripts; add fixtures for new patterns.

## Official Sources Used

Read and checked on 2026-10-03 for this revision:

- Metadata API Developer Guide, Summer '26 (API 67.0), AiEvaluationDefinition (fields, `subjectVersion` default, API 63.0 availability): https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf
- Agentforce Developer Guide, Build Tests in Metadata API (test case inputs, context variables, conversation history, sample definition): https://developer.salesforce.com/docs/ai/agentforce/guide/testing-api-build-tests.html
- Agentforce Developer Guide, Add Custom Evaluation Criteria to a Test Case (string and numeric operators, 100-character parameters, JSONPath into generatedData): https://developer.salesforce.com/docs/ai/agentforce/guide/testing-api-custom-evaluation-criteria.html
- Agentforce Developer Guide, Considerations for the Testing API (Einstein Requests in sandboxes, 10 in-progress runs, 1,000 test cases, results may change): https://developer.salesforce.com/docs/ai/agentforce/guide/testing-api-considerations.html
- Agentforce Developer Guide, Use Test Results to Improve Your Agent (what each expectation measures, semantic outcome test, PASS or FAILED): https://developer.salesforce.com/docs/ai/agentforce/guide/testing-api-use-results.html
- Agentforce Developer Guide, Deploy and Run Tests in the Command Line (API name of Agentforce (Default) is Copilot_for_Salesforce): https://developer.salesforce.com/docs/ai/agentforce/guide/testing-api-cli.html
- Agentforce Developer Guide, Run Agent Tests (sf agent test run, resume, results, retrieve): https://developer.salesforce.com/docs/ai/agentforce/guide/agent-dx-test-run.html
- Agentforce Developer Guide, Generate a Test Spec File (legacy versus new testing process, required spec fields): https://developer.salesforce.com/docs/ai/agentforce/guide/agent-dx-test-spec.html
- Agentforce Developer Guide, Troubleshoot Agentforce DX Issues (exit code 1 semantics, publish and activate before testing): https://developer.salesforce.com/docs/ai/agentforce/guide/agent-dx-troubleshooting.html
- Agentforce Developer Guide, Headless Example: Optimize an Agent by Analyzing Production Data (no raw production transcripts in test cases, sandbox first, full-suite gate): https://developer.salesforce.com/docs/ai/agentforce/guide/headless-examples-agent-optimize.html
- Agentforce Developer Guide, Export Agentforce Session Tracing Data (Beta) (settings required to read traces): https://developer.salesforce.com/docs/ai/agentforce/guide/otel-api.html
- Generative AI guide, Spring '26, Troubleshooting Agents and Agentforce Analytics (non-determinism, Utterance Analysis clusters): https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/generative_ai.pdf
- Salesforce CLI help text, `sf agent activate --help` and `sf agent test run --help` (CLI 2.151.7: `--version` is the number of `vX`; result formats json, human, junit, tap)

### Carried forward from earlier versions (not re-read on 2026-10-03)

These were not re-read for this revision. help.salesforce.com articles do not return their text to a fetch, so claims that rest only on a Help article are marked UNVERIFIED in the skill.

- Salesforce Help — Agentforce Testing Center: https://help.salesforce.com/s/articleView?id=sf.copilot_testing.htm
- Salesforce Developer — Einstein Trust Layer: https://developer.salesforce.com/docs/einstein/genai/guide/trust-layer.html
- Salesforce Architects — Evaluating AI Systems: https://architect.salesforce.com/
- Salesforce Developer — Agentforce Developer Guide: https://developer.salesforce.com/docs/einstein/genai/guide/
