# Agentforce Eval Harness: Work Template

Use this template when building or extending an eval harness for one agent.

## Scope

**Skill:** `agentforce-eval-harness`

**Agent API name and pinned version:** (for example `Returns_Service_Agent`, `v3`)

**Eval sandbox alias:** (never a production org)

## Answers to the Questions to Ask

| Question | Answer |
|---|---|
| Agent version under test and who bumps it | |
| Eval sandbox and per-PR budget | |
| Subagents and actions in scope | |
| Test-data source rule (synthesized or scrubbed) | |
| CI gate (JSON or JUnit parsing of `metricScore`) | |
| Deterministic checks versus judged checks | |

## Coverage Plan

| Subagent API name | P0 cases (at least 2) | Negative or refusal case | Actions exercised |
|---|---|---|---|
| | | | |

## Rubric

| Dimension | 0 | 1 | 2 | Anti-example |
|---|---|---|---|---|
| correctness | | | | |
| grounding | | | | |
| tone | | | | |

## Checklist

- [ ] Every subagent has at least two P0 fixtures and one negative case.
- [ ] Every action is exercised by at least one fixture.
- [ ] Fixtures contain no record IDs and no personal data.
- [ ] `AiEvaluationDefinition` pins `subjectVersion` and stays under 1,000 cases.
- [ ] `scripts/check_agentforce_eval_harness.py --manifest-dir <dir>` reports no ERROR.
- [ ] CI parses each `metricScore` and treats exit code 1 as an execution error.
- [ ] Judge calibration against 20 human-scored cases reached 80 percent agreement or better.

## Deviations

Record any departure from the patterns in SKILL.md and the reason for it.
