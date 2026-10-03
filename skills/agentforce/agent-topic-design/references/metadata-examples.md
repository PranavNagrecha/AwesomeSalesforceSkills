# Metadata Examples: Agent Topic Design

Three deployable artifacts for one subagent design: the topic as `GenAiPlugin` metadata, the same routing expressed in Agent Script, and a routing test. Field names and structures follow the Metadata API Developer Guide (Spring '26: GenAiPlugin, GenAiPluginInstructionDef, AiPluginUtteranceDef, AiEvaluationDefinition, AiAuthoringBundle) and the Agentforce Developer Guide (Agent Script).

## 1. Topic as GenAiPlugin metadata (asset-library topic, API 63.0+ for utterances)

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!-- force-app/main/default/genAiPlugins/Order_Returns.genAiPlugin-meta.xml -->
<GenAiPlugin xmlns="http://soap.sforce.com/2006/04/metadata">
    <aiPluginUtterances>
        <developerName>return_my_order</developerName>
        <language>en_US</language>
        <masterLabel>return my order</masterLabel>
        <utterance>I want to return the shoes I bought last week</utterance>
    </aiPluginUtterances>
    <aiPluginUtterances>
        <developerName>return_label</developerName>
        <language>en_US</language>
        <masterLabel>return label</masterLabel>
        <utterance>Can you send me a return label for order 1042?</utterance>
    </aiPluginUtterances>
    <canEscalate>true</canEscalate>
    <description>Handles returns for orders placed in the last 90 days: checking return eligibility, creating a return label, and reporting the status of an existing return. Does not handle exchanges, refunds to a different payment method, or damaged-item claims.</description>
    <developerName>Order_Returns</developerName>
    <genAiFunctions>
        <functionName>Check_Return_Eligibility</functionName>
    </genAiFunctions>
    <genAiFunctions>
        <functionName>Create_Return_Label</functionName>
    </genAiFunctions>
    <genAiFunctions>
        <functionName>Get_Return_Status</functionName>
    </genAiFunctions>
    <genAiPluginInstructions>
        <description>As a first step, get the order number. If the user only gives a product name, ask which order it was on before calling any action.</description>
        <developerName>get_order_first</developerName>
        <language>en_US</language>
        <masterLabel>get order first</masterLabel>
        <sortOrder>1</sortOrder>
    </genAiPluginInstructions>
    <genAiPluginInstructions>
        <description>Always call Check_Return_Eligibility before Create_Return_Label. If the result says the order is not eligible, explain the reason it returns and offer to connect the user with a service rep.</description>
        <developerName>check_before_label</developerName>
        <language>en_US</language>
        <masterLabel>check before label</masterLabel>
        <sortOrder>2</sortOrder>
    </genAiPluginInstructions>
    <genAiPluginInstructions>
        <description>If the user asks about an exchange, a refund to another card, or a damaged item, say this topic cannot help with that and offer a service rep.</description>
        <developerName>out_of_scope</developerName>
        <language>en_US</language>
        <masterLabel>out of scope</masterLabel>
        <sortOrder>3</sortOrder>
    </genAiPluginInstructions>
    <language>en_US</language>
    <masterLabel>Order Returns</masterLabel>
    <pluginType>Topic</pluginType>
    <scope>Your job is to only handle returns for orders placed in the last 90 days: check eligibility, create return labels, and report return status. You are not allowed to issue refunds, start exchanges, or change order details.</scope>
</GenAiPlugin>
```

Design notes tied to the gotchas:

- `description` is the classification description the agent compares utterances against. It names what is in and what is out.
- The 90-day rule is enforced by the `Check_Return_Eligibility` action, not by an instruction; the instruction only says to call it first.
- Sequence is stated inside the instructions in words. `sortOrder` is set, but the Generative AI guide says the LLM does not use instruction order to decide.
- Three actions, well under the guide's recommended ceiling of 15 per topic. The three `GenAiFunction` components must exist (or deploy in the same package).
- In Winter '26 and later, a topic created inside one agent is retrieved through that agent's `GenAiPlannerBundle`; this asset-library form is what `GenAiPlugin` retrieves.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!-- manifest/package.xml -->
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>Check_Return_Eligibility</members>
        <members>Create_Return_Label</members>
        <members>Get_Return_Status</members>
        <name>GenAiFunction</name>
    </types>
    <types>
        <members>Order_Returns</members>
        <name>GenAiPlugin</name>
    </types>
    <version>65.0</version>
</Package>
```

UNVERIFIED (2026-10-03): the `.genAiPlugin-meta.xml` file name under `force-app` follows the source-format convention for the documented `.genAiPlugin` suffix and `genAiPlugins` folder.

## 2. The same routing in Agent Script

For agents authored in Agent Script, routing lives in the agent router (`start_agent`) and each subagent declares its own description. The structure below follows the Agent Router, Transitions, and Utils pages of the Agentforce Developer Guide.

```text
# force-app/main/default/aiAuthoringBundles/Retail_Service_Agent/Retail_Service_Agent.agent  (excerpt)
start_agent agent_router:
  description: "Welcome the user and route to the appropriate subagent"

  reasoning:
    instructions: ->
      | Select the best tool to call based on conversation history and user's intent.

    actions:
      go_to_returns: @utils.transition to @subagent.Order_Returns
        description: "Handles return eligibility, return labels, and return status for orders from the last 90 days."
      go_to_escalation: @utils.transition to @subagent.Escalation
        description: "Escalate to a human representative."

subagent Order_Returns:
  description: "Handles return eligibility, return labels, and return status for orders placed in the last 90 days."

  reasoning:
    instructions: ->
      | As a first step, get the order number.
      | If the user asks about an exchange or a damaged item, call {!@actions.go_to_escalation}.

    actions:
      go_to_escalation: @utils.transition to @subagent.Escalation
        description: "Escalate if the request is out of scope for returns."
```

Transitions are one way: when `Order_Returns` hands off, control does not come back unless another transition routes it back, and a return starts at the top of the subagent (Agent Script Reference: Utils).

## 3. Routing regression test

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!-- force-app/main/default/aiEvaluationDefinitions/Order_Returns_Routing.aiEvaluationDefinition-meta.xml -->
<AiEvaluationDefinition xmlns="http://soap.sforce.com/2006/04/metadata">
    <description>Routing checks for the Order Returns subagent and its neighbours.</description>
    <name>Order_Returns_Routing</name>
    <subjectName>Retail_Service_Agent</subjectName>
    <subjectType>AGENT</subjectType>
    <subjectVersion>v1</subjectVersion>
    <testCase>
        <number>1</number>
        <inputs>
            <utterance>Can you send me a return label for order 1042?</utterance>
        </inputs>
        <expectation>
            <name>topic_sequence_match</name>
            <expectedValue>Order_Returns</expectedValue>
        </expectation>
        <expectation>
            <name>action_sequence_match</name>
            <expectedValue>["Check_Return_Eligibility","Create_Return_Label"]</expectedValue>
        </expectation>
    </testCase>
    <testCase>
        <number>2</number>
        <inputs>
            <utterance>The blender arrived broken, I want a new one</utterance>
        </inputs>
        <expectation>
            <name>topic_sequence_match</name>
            <expectedValue>Escalation</expectedValue>
        </expectation>
    </testCase>
</AiEvaluationDefinition>
```

Run it after every topic addition or classification description edit. The test definition shape (subject, test cases, `topic_sequence_match`, `action_sequence_match`) follows the AiEvaluationDefinition sample in the Agentforce Developer Guide, Build Tests in Metadata API.
