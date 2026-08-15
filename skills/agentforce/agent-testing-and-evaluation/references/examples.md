# Examples — Agent Testing and Evaluation

## Example 1: Minimal AiEvaluationDefinition for Subagent Routing Validation

**Context:** A service agent has three subagents (called topics before April 2026, and still called that by the metadata fields below): `OrderStatus`, `ReturnRequest`, and `BillingInquiry`. The team wants automated confirmation that utterances route to the correct subagent before every production promotion.

**Problem:** Without structured tests, subagent routing regressions are only caught by QA testers manually chatting with the agent — which is slow, non-repeatable, and misses edge cases.

**Solution:**

```xml
<!-- AiEvaluationDefinition metadata file: OrderAgentTopicTests.aiEvaluationDefinition-meta.xml -->
<?xml version="1.0" encoding="UTF-8"?>
<AiEvaluationDefinition xmlns="http://soap.sforce.com/2006/04/metadata">
    <name>OrderAgentTopicTests</name>
    <subjectType>AGENT</subjectType>
    <subjectName>OrderServiceAgent</subjectName>
    <testCases>
        <!-- Happy path: OrderStatus -->
        <testCase>
            <inputs>
                <utterance>Where is my order?</utterance>
            </inputs>
            <expectations>
                <expectTopicName>OrderStatus</expectTopicName>
            </expectations>
        </testCase>
        <!-- Edge case: OrderStatus with paraphrase -->
        <testCase>
            <inputs>
                <utterance>Can you tell me when my package will arrive</utterance>
            </inputs>
            <expectations>
                <expectTopicName>OrderStatus</expectTopicName>
            </expectations>
        </testCase>
        <!-- Boundary: ReturnRequest near BillingInquiry -->
        <testCase>
            <inputs>
                <utterance>I was charged twice and want my money back</utterance>
            </inputs>
            <expectations>
                <expectTopicName>ReturnRequest</expectTopicName>
            </expectations>
        </testCase>
        <!-- Happy path: BillingInquiry -->
        <testCase>
            <inputs>
                <utterance>I have a question about my invoice</utterance>
            </inputs>
            <expectations>
                <expectTopicName>BillingInquiry</expectTopicName>
            </expectations>
        </testCase>
    </testCases>
</AiEvaluationDefinition>
```

```bash
# Deploy the test definition alongside agent metadata
sf project deploy start --source-dir force-app/main/default/aiEvaluationDefinitions

# Execute the test suite via Connect API (replace ORG_DOMAIN and SESSION_ID)
curl -X POST \
  https://ORG_DOMAIN.my.salesforce.com/services/data/v63.0/einstein/ai-evaluations/runs \
  -H "Authorization: Bearer SESSION_ID" \
  -H "Content-Type: application/json" \
  -d '{"aiEvaluationName": "OrderAgentTopicTests"}'

# Returns: { "jobId": "0Xx..." }

# Poll for results
curl https://ORG_DOMAIN.my.salesforce.com/services/data/v63.0/einstein/ai-evaluations/runs/0Xx... \
  -H "Authorization: Bearer SESSION_ID"
```

**Why it works:** The `AiEvaluationDefinition` is version-controlled alongside the agent metadata. Every promotion deploys the latest test definition and executes it. Subagent routing failures surface before production, not after.

---

## Example 2: Multi-Turn Conversation Test for a Context-Dependent Return Flow

**Context:** The `ReturnRequest` subagent requires the agent to first retrieve an order before it can process a return. The second user message ("yes, that one") is only meaningful if the agent correctly surfaced the order details in the first turn.

**Problem:** Single-utterance tests cannot catch failures in turn 2 that depend on turn 1 context. A team testing only the opening utterance will miss cases where the agent "forgets" context mid-conversation.

**Solution:**

```xml
<testCase>
    <inputs>
        <utterance>Yes, please start the return for order 1001</utterance>
        <conversationHistory>
            <turn>
                <role>user</role>
                <content>I want to return something</content>
            </turn>
            <turn>
                <role>agent</role>
                <content>I found order 1001 placed on March 15. Is this the order you want to return?</content>
            </turn>
        </conversationHistory>
    </inputs>
    <expectations>
        <expectTopicName>ReturnRequest</expectTopicName>
        <expectActions>
            <action>InitiateReturn</action>
        </expectActions>
    </expectations>
</testCase>
```

**Why it works:** The `conversationHistory` array puts the agent in the correct conversational state before the test utterance is evaluated. The test confirms both that the subagent persists through the context and that the `InitiateReturn` action is invoked in the right step — not just in a fresh session.

---

## Example 3: CLI-Native CI Gate with Agentforce DX

**Context:** The team from Example 1 wants the topic test suite to gate every promotion from the CI sandbox, without maintaining a custom curl-and-poll script.

**Problem:** The raw Connect API approach requires the pipeline to manage a session token, poll the job ID in a loop, and parse the result JSON to decide pass/fail — three pieces of bespoke scripting that the Salesforce CLI already provides.

**Solution:**

```bash
# One-time authoring (developer workstation):
# scaffold a test spec YAML listing the test cases for the agent
sf agent generate test-spec

# create the test in the dev org from the spec — this also syncs the
# resulting AiEvaluationDefinition metadata back into the DX project,
# so the test is version-controlled without a manual retrieve
sf agent test create   # pass the generated test spec file

# Pipeline stage (CI runner):
# deploy the test definition alongside the agent metadata
sf project deploy start --source-dir force-app/main/default/aiEvaluationDefinitions

# run synchronously; write JUnit result files the CI runner parses natively
sf agent test run --api-name OrderAgentTopicTests --target-org ci-sandbox \
  --wait 10 --result-format junit --output-dir ./agent-test-results
```

```bash
# Async variant for long suites: submit now, collect in a later stage.
# Without --wait, the run command prints the resume command and exits.
sf agent test run --api-name OrderAgentTopicTests --target-org ci-sandbox
# ...later stage:
sf agent test results --job-id <jobId>

# Discover test API names available in the target org before running
sf agent test list
```

**Why it works:** `--wait` makes the run command block until completion, so the pipeline step itself gates promotion; `--result-format junit` plus `--output-dir` produces result files that CI systems (Jenkins, GitHub Actions, GitLab) parse without custom code. The CLI reuses the runner's existing org auth — no session-token handling. Keep `sf api request rest` (or raw curl) only for Connect API endpoints the `sf agent test` family doesn't wrap, such as pulling the full Get Test Results payload by `runId` for baseline archiving.

---

## Anti-Pattern: Testing Only the Agent's Happy Path Utterances

**What practitioners do:** They write one test per subagent using the most obvious phrasing — "track my order", "I want to return something", "billing question" — and declare the agent ready for production when all three pass.

**What goes wrong:** Real customers use unexpected phrasings, abbreviations, and mixed-intent messages ("I got the wrong item and was overcharged"). Happy-path-only test suites give false confidence. The first sprint after go-live fills with escalation reports for utterances the team never tested.

**Correct approach:** Apply the 4-type utterance model: happy path (2), edge case (2), boundary near adjacent subagents (1+), and out-of-scope (1+) per subagent. Boundary and out-of-scope utterances expose the routing failures that produce production incidents. Treat a coverage matrix as a required deliverable alongside the test code.
