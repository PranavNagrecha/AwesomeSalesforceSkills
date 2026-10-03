# Metadata Examples: Agentforce Multi-Turn Patterns

A return-request agent written in Agent Script, deployed as an `AiAuthoringBundle`, and tested with a multi-turn `AiEvaluationDefinition`. Block names and syntax follow the Agentforce Developer Guide (Agent Script Blocks, Variables, Utils, Actions, Transitions); the bundle layout and fields follow the Metadata API Developer Guide (Spring '26), AiAuthoringBundle (API 65.0+).

## 1. Bundle layout

```text
force-app/main/default/aiAuthoringBundles/
  Returns_Agent/
    Returns_Agent.agent            Agent Script definition (below)
    Returns_Agent.bundle-meta.xml  bundle metadata (below)
```

## 2. Bundle metadata (draft version)

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!-- force-app/main/default/aiAuthoringBundles/Returns_Agent/Returns_Agent.bundle-meta.xml -->
<AiAuthoringBundle xmlns="http://soap.sforce.com/2006/04/metadata">
    <bundleType>AGENT</bundleType>
    <versionDescription>Return flow with cascade reset and verified-account reuse.</versionDescription>
</AiAuthoringBundle>
```

`target` is omitted, which the Metadata API guide says deploys the agent in draft state. Publishing with Agentforce DX fills `target` as `{Bot}.{BotVersion}`, which is the same as Commit Version in Agentforce Builder.

## 3. Agent Script

```text
# force-app/main/default/aiAuthoringBundles/Returns_Agent/Returns_Agent.agent
system:
    instructions: "You help customers return items from recent orders. Be brief and confirm before acting."
    messages:
        welcome: "Hi! I can help you return an item. What's your order number?"
        error: "Sorry, something went wrong. Let me try that again."

config:
    developer_name: "Returns_Agent"
    agent_label: "Returns Agent"
    description: "Collects order, item, and reason across turns and creates a return."
    runtime:
        reset_to_initial_node: False

connection messaging:
    escalation_message: "One moment while I connect you to a service representative."
    outbound_route_type: "OmniChannelFlow"
    outbound_route_name: "Returns_Escalation_Flow"

variables:
    order_number: mutable string = ""
        description: "Order the customer wants to return from. Source of truth for item_id and return_reason."
    item_id: mutable string = ""
        description: "Record ID of the order item being returned. Derived from order_number."
    return_reason: mutable string = ""
        description: "Reason the customer gave for the return."
    verified_account_id: mutable string = ""
        description: "Account ID set after identity verification. Read by every subagent."
    messaging_session_id: linked string
        source: @MessagingSession.Id
        description: "Messaging session for this conversation."

start_agent agent_router:
    description: "Welcome the customer and route to the right subagent"
    reasoning:
        instructions: ->
            if @variables.verified_account_id == "":
                transition to @subagent.Identity
            | Select the best tool to call based on conversation history and user's intent.
        actions:
            go_to_returns: @utils.transition to @subagent.Returns
                description: "Handles item returns for an order."
            go_to_escalation: @utils.escalate
                description: "Escalate to a human rep when the customer asks for one."

subagent Identity:
    description: "Verifies the customer before any order data is shown."
    reasoning:
        instructions: ->
            | Ask for the email on the account, then call {!@actions.verify_customer}.
        actions:
            verify_customer: @actions.verify_customer
                with email = ...
                set @variables.verified_account_id = @outputs.account_id
                transition to @subagent.Returns
    actions:
        verify_customer:
            description: "Verify the customer by email and return the account ID."
            inputs:
                email: string
            outputs:
                account_id: string
                date_of_birth: string
                    filter_from_agent: True
            target: "apex://VerifyCustomerAction"

subagent Returns:
    description: "Collects the order number, the item, and the reason, then creates the return."
    reasoning:
        instructions: ->
            if @variables.order_number == "":
                | Ask for the order number, then call {!@actions.capture_order}.
            if @variables.order_number != "" and @variables.item_id == "":
                | Show the items on order {!@variables.order_number} and ask which one is being returned, then call {!@actions.capture_item}.
            if @variables.item_id != "" and @variables.return_reason == "":
                | Ask why the item is being returned, then call {!@actions.capture_reason}.
            | Confirm order, item, and reason before calling {!@actions.create_return}.
              If the customer changes the order number, call {!@actions.capture_order} again.
        actions:
            capture_order: @utils.setVariables
                with order_number = ...
                description: "Store the order number the customer gave."
            capture_item: @utils.setVariables
                with item_id = ...
                description: "Store the record ID of the item the customer picked."
            capture_reason: @utils.setVariables
                with return_reason = ...
                description: "Store the reason for the return."
            create_return: @actions.create_return
                with order_number = @variables.order_number
                with item_id = @variables.item_id
                with reason = @variables.return_reason
    actions:
        create_return:
            description: "Create a return for one order item."
            inputs:
                order_number: string
                item_id: string
                reason: string
            outputs:
                return_id: string
            target: "flow://Create_Order_Return"
```

What each part demonstrates:

- `variables` is agent-wide. `verified_account_id` set in `Identity` is visible in `Returns` with no extra wiring.
- The `Returns` instructions branch on which variables are still empty, so a detour to `Identity` and back resumes at the first missing fact instead of starting over (transitions restart a subagent from the top).
- `order_number` is the source of truth. The instruction tells the agent to re-capture it on a correction, and the design rule is that `item_id` and `return_reason` are cleared with it.
- `messaging_session_id` is a linked variable: no default, not settable by the agent, sourced from `@MessagingSession`.
- `date_of_birth` is returned for verification but kept out of the model's context with `filter_from_agent: True`, because action outputs otherwise stay in context for the session.
- `reset_to_initial_node: False` keeps each turn resuming where the last one stopped.
- `@utils.escalate` relies on the `connection messaging` block with `outbound_route_type` and `outbound_route_name`.
- Record IDs are `string`; the `id` type is deprecated.

UNVERIFIED (2026-10-03): this file combines documented constructs into one agent; validate it with Agentforce DX before relying on it. Two details are not shown verbatim in the guide pages read: the declaration form of the linked variable (`linked string` with a `source:` line; the guide documents linked variables, their restrictions, and the `@MessagingSession` source namespace) and the `apex://VerifyCustomerAction` target (the guide documents the `{TARGET_TYPE}://{DEVELOPER_NAME}` format with `apex` as a valid type). The `!=` and `and` operators are documented on the Conditional Expressions reference page. The reset of `item_id` and `return_reason` on a corrected order number is stated as an instruction here; enforce it deterministically with `set` statements once the capturing action and its outputs are in place.

## 4. Multi-turn test

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!-- force-app/main/default/aiEvaluationDefinitions/Returns_Agent_Multi_Turn.aiEvaluationDefinition-meta.xml -->
<AiEvaluationDefinition xmlns="http://soap.sforce.com/2006/04/metadata">
    <description>Correction mid-flow keeps the agent in Returns and re-captures the order.</description>
    <name>Returns_Agent_Multi_Turn</name>
    <subjectName>Returns_Agent</subjectName>
    <subjectType>AGENT</subjectType>
    <subjectVersion>v1</subjectVersion>
    <testCase>
        <number>1</number>
        <inputs>
            <conversationHistory>
                <role>user</role>
                <message>I want to return something from order A7842</message>
                <index>0</index>
            </conversationHistory>
            <conversationHistory>
                <role>agent</role>
                <message>Order A7842 has a Blue Scarf and a Wool Hat. Which one are you returning?</message>
                <topic>Returns</topic>
                <index>1</index>
            </conversationHistory>
            <utterance>Sorry, it was actually order A7843</utterance>
        </inputs>
        <expectation>
            <name>topic_sequence_match</name>
            <expectedValue>Returns</expectedValue>
        </expectation>
        <expectation>
            <name>action_sequence_match</name>
            <expectedValue>["capture_order"]</expectedValue>
        </expectation>
    </testCase>
</AiEvaluationDefinition>
```

The `conversationHistory` element (role, message, subagent in `topic` for agent turns, index) is the documented way to test an utterance inside a conversation (Agentforce Developer Guide, Build Tests in Metadata API).

## 5. package.xml member form

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!-- manifest/package.xml -->
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>Returns_Agent</members>
        <name>AiAuthoringBundle</name>
    </types>
    <types>
        <members>Returns_Agent_Multi_Turn</members>
        <name>AiEvaluationDefinition</name>
    </types>
    <version>65.0</version>
</Package>
```

The `AiAuthoringBundle` member is the bundle folder name, as in the guide's `New_Agent` sample. The flow `Create_Order_Return`, the Apex class `VerifyCustomerAction`, and the Omni-Channel flow `Returns_Escalation_Flow` must exist in the org or be deployed with the bundle.
