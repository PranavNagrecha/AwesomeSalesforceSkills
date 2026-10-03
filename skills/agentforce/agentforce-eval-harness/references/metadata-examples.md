# Metadata Examples: Agentforce Eval Harness

The harness in `SKILL.md` has two layers. The deterministic layer (which subagent, which actions, which arguments) maps onto the platform's own test metadata, `AiEvaluationDefinition`. The judgement layer (rubric scores from a human or an LLM judge) stays in the harness. This file shows the deterministic layer as deployable metadata so CI can run it with `sf agent test run`.

Running and reading Testing Center results in depth belongs to `agentforce/agent-testing-and-evaluation`. This file covers how a harness fixture becomes a deployable regression definition.

## Example 1: A regression definition for a returns agent

**Context.** A service agent with API name `Returns_Service_Agent` has an `Order_Returns` subagent with two actions, `Look_Up_Order` and `Start_Return`. Version `v3` is the version under test. The harness already holds markdown fixtures for the same behaviour; this definition is their deterministic projection.

**File path:** `force-app/main/default/aiEvaluationDefinitions/Returns_Agent_Regression.aiEvaluationDefinition-meta.xml`

The `aiEvaluationDefinitions` folder and the `.aiEvaluationDefinition` suffix come from the Metadata API reference. The `-meta.xml` ending is the standard source-format convention for a DX project.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<AiEvaluationDefinition xmlns="http://soap.sforce.com/2006/04/metadata">
    <description>P0 regression cases for the returns subagent, projected from the harness fixtures</description>
    <name>Returns_Agent_Regression</name>
    <subjectName>Returns_Service_Agent</subjectName>
    <subjectType>AGENT</subjectType>
    <subjectVersion>v3</subjectVersion>
    <testCase>
        <number>1</number>
        <inputs>
            <utterance>I want to return the blender from my last order</utterance>
        </inputs>
        <expectation>
            <name>topic_sequence_match</name>
            <expectedValue>Order_Returns</expectedValue>
        </expectation>
        <expectation>
            <name>action_sequence_match</name>
            <expectedValue>["Look_Up_Order"]</expectedValue>
        </expectation>
        <expectation>
            <name>bot_response_rating</name>
            <expectedValue>The agent asks for the order number before taking any action and does not invent one</expectedValue>
        </expectation>
        <expectation>
            <name>coherence</name>
        </expectation>
    </testCase>
    <testCase>
        <number>2</number>
        <inputs>
            <utterance>Yes, go ahead and start the return</utterance>
            <conversationHistory>
                <role>user</role>
                <message>I want to return order A7842</message>
                <index>0</index>
            </conversationHistory>
            <conversationHistory>
                <role>agent</role>
                <message>I found order A7842 with one blender. Do you want me to start a return for it?</message>
                <topic>Order_Returns</topic>
                <index>1</index>
            </conversationHistory>
        </inputs>
        <expectation>
            <name>action_sequence_match</name>
            <expectedValue>["Start_Return"]</expectedValue>
        </expectation>
        <expectation>
            <label>return started for the confirmed order</label>
            <name>string_comparison</name>
            <parameter>
                <name>operator</name>
                <value>equals</value>
                <isReference>false</isReference>
            </parameter>
            <parameter>
                <name>actual</name>
                <value>$.generatedData.invokedActions[*][?(@.function.name == 'Start_Return')].function.input.orderNumber</value>
                <isReference>true</isReference>
            </parameter>
            <parameter>
                <name>expected</name>
                <value>A7842</value>
                <isReference>false</isReference>
            </parameter>
        </expectation>
    </testCase>
    <testCase>
        <number>3</number>
        <inputs>
            <utterance>Should I sue the courier for losing my parcel?</utterance>
        </inputs>
        <expectation>
            <name>action_sequence_match</name>
            <expectedValue>[]</expectedValue>
        </expectation>
        <expectation>
            <name>bot_response_rating</name>
            <expectedValue>The agent declines to give legal advice, acknowledges the frustration, and offers to open a lost-parcel claim</expectedValue>
        </expectation>
    </testCase>
    <testCase>
        <number>4</number>
        <inputs>
            <utterance>What is the status of my return?</utterance>
        </inputs>
        <expectation>
            <name>topic_sequence_match</name>
            <expectedValue>Order_Returns</expectedValue>
        </expectation>
        <expectation>
            <name>output_latency_milliseconds</name>
        </expectation>
    </testCase>
</AiEvaluationDefinition>
```

**Why each element is there.**

| Element | Why | Source |
|---|---|---|
| `subjectType` = `AGENT` | The only supported value | Metadata API reference, AiEvaluationDefinition fields |
| `subjectVersion` = `v3` | Without it the latest active version is tested, so the baseline moves when someone activates a new version | Metadata API reference, `subjectVersion` |
| `conversationHistory` in case 2 | Multi-turn context; an `agent` turn carries the subagent it used | Agentforce Developer Guide, Build Tests in Metadata API |
| `string_comparison` in case 2 | Asserts the action argument, the harness's deterministic tool-call check | Agentforce Developer Guide, Add Custom Evaluation Criteria |
| `action_sequence_match` = `[]` in case 3 | A negative case: no action may fire for an out-of-scope request | Agentforce Developer Guide, Build Tests in Metadata API (pizza-recipe sample) |
| Quality metrics with no `expectedValue` | `coherence` and `output_latency_milliseconds` need no expected value | Agentforce Developer Guide, Use Test Results to Improve Your Agent |

Action names in `action_sequence_match` and in the JSONPath filter must be the API names the planner reports. UNVERIFIED (2026-10-03): whether a custom action in an unmanaged org needs a namespace prefix in these values; the documented JSONPath pattern shows `namespace_actionName`. Confirm by running one case with `--verbose` and reading `generatedData`.

## package.xml member form

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>Returns_Agent_Regression</members>
        <name>AiEvaluationDefinition</name>
    </types>
    <version>66.0</version>
</Package>
```

`AiEvaluationDefinition` is available from API version 63.0. The `parameter` element used by custom evaluations needs API version 64.0 or later, so the manifest uses 66.0.

## Deploy order and run

1. The agent `Returns_Service_Agent` version `v3` must already exist in the target org. A test definition against an agent that is not published fails at create time.
2. Activate the agent version. Some tests need an active agent, and CI scripts should activate before running. The `--version` value is the number from the `vX` version name (Salesforce CLI `sf agent activate --help`).
3. Deploy the definition, then run it and keep the JSON for the harness diff:

```bash
sf project deploy start --manifest manifest/package.xml --target-org eval-sbx
sf agent activate --api-name Returns_Service_Agent --version 3 --target-org eval-sbx
sf agent test run --api-name Returns_Agent_Regression --target-org eval-sbx \
  --wait 20 --result-format json --output-dir results/returns
```

4. For a CI dashboard, `--result-format junit` is also accepted (Salesforce CLI `sf agent test run --help`).
5. Read the exit code with care. Exit code 1 from `sf agent test run` means test cases hit execution errors. It does not mean assertions failed. The harness must parse the JSON result for each `metricScore` (PASS or FAILED) before it decides to block the PR.

## Verification

- `sf project retrieve start --metadata AiEvaluationDefinition --target-org eval-sbx` returns `Returns_Agent_Regression` unchanged.
- `python3 skills/agentforce/agentforce-eval-harness/scripts/check_agentforce_eval_harness.py --manifest-dir force-app` reports no ERROR lines.
- In the JSON result, case 3 shows no invoked action, and case 2 shows `Start_Return` called with `A7842`.

## Mapping a harness fixture onto the definition

| Harness fixture field | AiEvaluationDefinition element | Notes |
|---|---|---|
| `topic:` | `topic_sequence_match` expectation | The fixture key keeps the old name; the value is the subagent API name |
| `expected_tool_calls[].tool` | `action_sequence_match` expectation | A JSON-style list literal, `[]` for "no action" |
| `expected_tool_calls[].args` | `string_comparison` or `numeric_comparison` | One custom expectation per asserted argument; each parameter value is limited to 100 characters |
| Rubric dimension `grounding` / `tone` | `bot_response_rating` plus the harness judge | `bot_response_rating` is a semantic comparison, so keep the rubric score in the harness |
| Multi-turn input transcript | `conversationHistory` entries | Index from 0; an `agent` entry names its subagent |
| Reference answer placeholders | Not supported | Resolve `{{testOrder.orderNumber}}` before generating the XML |
