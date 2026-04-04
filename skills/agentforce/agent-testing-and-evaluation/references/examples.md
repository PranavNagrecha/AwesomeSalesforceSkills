# Examples — Agent Testing and Evaluation

## Example 1: Minimal AiEvaluationDefinition for Topic Routing Validation

**Context:** A service agent has three topics: `OrderStatus`, `ReturnRequest`, and `BillingInquiry`. The team wants automated confirmation that utterances route to the correct topic before every production promotion.

**Problem:** Without structured tests, topic routing regressions are only caught by QA testers manually chatting with the agent — which is slow, non-repeatable, and misses edge cases.

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
  https://ORG_DOMAIN.my.salesforce.com/services/data/v62.0/connect/einstein/ai-evaluations \
  -H "Authorization: Bearer SESSION_ID" \
  -H "Content-Type: application/json" \
  -d '{"aiEvaluationName": "OrderAgentTopicTests"}'

# Returns: { "jobId": "0Xx..." }

# Poll for results
curl https://ORG_DOMAIN.my.salesforce.com/services/data/v62.0/connect/einstein/ai-evaluations/0Xx... \
  -H "Authorization: Bearer SESSION_ID"
```

**Why it works:** The `AiEvaluationDefinition` is version-controlled alongside the agent metadata. Every promotion deploys the latest test definition and executes it. Topic routing failures surface before production, not after.

---

## Example 2: Multi-Turn Conversation Test for a Context-Dependent Return Flow

**Context:** The `ReturnRequest` topic requires the agent to first retrieve an order before it can process a return. The second user message ("yes, that one") is only meaningful if the agent correctly surfaced the order details in the first turn.

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

**Why it works:** The `conversationHistory` array puts the agent in the correct conversational state before the test utterance is evaluated. The test confirms both that the topic persists through the context and that the `InitiateReturn` action is invoked in the right step — not just in a fresh session.

---

## Anti-Pattern: Testing Only the Agent's Happy Path Utterances

**What practitioners do:** They write one test per topic using the most obvious phrasing — "track my order", "I want to return something", "billing question" — and declare the agent ready for production when all three pass.

**What goes wrong:** Real customers use unexpected phrasings, abbreviations, and mixed-intent messages ("I got the wrong item and was overcharged"). Happy-path-only test suites give false confidence. The first sprint after go-live fills with escalation reports for utterances the team never tested.

**Correct approach:** Apply the 4-type utterance model: happy path (2), edge case (2), boundary near adjacent topics (1+), and out-of-scope (1+) per topic. Boundary and out-of-scope utterances expose the routing failures that produce production incidents. Treat a coverage matrix as a required deliverable alongside the test code.
