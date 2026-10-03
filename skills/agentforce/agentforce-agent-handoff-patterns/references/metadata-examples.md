# Metadata Examples: Agentforce Agent Handoff Patterns

Three artefacts make a handoff work end to end: an action that packages the context before the transfer, the routing that actually moves the conversation, and a fallback for when that routing is unavailable. This file shows each one.

## Example 1: Package the context, then escalate

**Context.** A service agent cannot approve refunds over its limit. Before the conversation goes to a person, the agent creates a case holding a structured summary, so the service rep does not ask the customer to repeat themselves. The Generative AI guide recommends exactly this for the Escalation topic: "add the actions required to gather information and create or update a record. This way, after the conversation is passed to a live service rep, they don't have to."

### 1. Apex action that writes the context package

**File path:** `force-app/main/default/classes/CreateEscalationCaseAction.cls`

```apex
public with sharing class CreateEscalationCaseAction {

    public class Request {
        @InvocableVariable(required=true label='Contact ID' description='The verified contact ID from the verification step. Never take it from the customer message.')
        public Id contactId;
        @InvocableVariable(required=true label='Customer Intent' description='One sentence: what the customer wants, in plain words.')
        public String customerIntent;
        @InvocableVariable(required=true label='What Was Tried' description='The actions already taken in this conversation and their results.')
        public String attemptSummary;
        @InvocableVariable(required=true label='Handoff Reason' description='One of: USER_REQUEST, POLICY_LIMIT, LOW_CONFIDENCE, OUT_OF_SCOPE, SYSTEM_ERROR.')
        public String handoffReason;
    }

    public class Result {
        @InvocableVariable(label='Case Number' description='The case number to tell the customer.')
        public String caseNumber;
        @InvocableVariable(label='Error' description='Empty on success. CREATE_FAILED when the case could not be saved; escalate anyway.')
        public String error;
    }

    private static final Set<String> REASONS = new Set<String>{
        'USER_REQUEST', 'POLICY_LIMIT', 'LOW_CONFIDENCE', 'OUT_OF_SCOPE', 'SYSTEM_ERROR'
    };

    @InvocableMethod(
        label='Create Escalation Case'
        description='Creates a case that summarizes the conversation for a service rep before the conversation is escalated. Use it only right before escalation. Does not escalate by itself.'
        category='Escalation'
    )
    public static List<Result> create(List<Request> requests) {
        List<Case> cases = new List<Case>();
        for (Request req : requests) {
            String reason = REASONS.contains(req.handoffReason) ? req.handoffReason : 'OUT_OF_SCOPE';
            cases.add(new Case(
                ContactId = req.contactId,
                Origin = 'Web',
                Subject = ('Agent handoff: ' + reason).left(255),
                Description = 'Customer intent: ' + req.customerIntent
                    + '\nWhat was tried: ' + req.attemptSummary
                    + '\nHandoff reason: ' + reason
            ));
        }
        Database.SaveResult[] saves = Database.insert(cases, false, AccessLevel.USER_MODE);

        Set<Id> ids = new Set<Id>();
        for (Database.SaveResult sr : saves) {
            if (sr.isSuccess()) {
                ids.add(sr.getId());
            }
        }
        Map<Id, Case> numbers = new Map<Id, Case>([SELECT Id, CaseNumber FROM Case WHERE Id IN :ids WITH USER_MODE]);

        List<Result> results = new List<Result>();
        for (Integer i = 0; i < saves.size(); i++) {
            Result res = new Result();
            if (saves[i].isSuccess() && numbers.containsKey(saves[i].getId())) {
                res.caseNumber = numbers.get(saves[i].getId()).CaseNumber;
                res.error = '';
            } else {
                res.error = 'CREATE_FAILED';
            }
            results.add(res);
        }
        return results;
    }
}
```

The case holds a summary, not the transcript; link the transcript record if the rep needs the full history. The handoff reason is a fixed vocabulary so reports can count why the agent hands off.

### 2. Test class

**File path:** `force-app/main/default/classes/CreateEscalationCaseActionTest.cls`

```apex
@IsTest
private class CreateEscalationCaseActionTest {

    @IsTest
    static void createsCaseWithStructuredSummary() {
        Contact c = new Contact(LastName = 'Handoff');
        insert c;

        CreateEscalationCaseAction.Request req = new CreateEscalationCaseAction.Request();
        req.contactId = c.Id;
        req.customerIntent = 'Refund of 450 dollars for a damaged blender';
        req.attemptSummary = 'Looked up the order; refund is above the agent limit';
        req.handoffReason = 'POLICY_LIMIT';

        Test.startTest();
        List<CreateEscalationCaseAction.Result> results =
            CreateEscalationCaseAction.create(new List<CreateEscalationCaseAction.Request>{ req });
        Test.stopTest();

        Assert.areEqual('', results[0].error);
        Case saved = [SELECT Subject, Description, ContactId FROM Case WHERE ContactId = :c.Id];
        Assert.areEqual('Agent handoff: POLICY_LIMIT', saved.Subject);
        Assert.isTrue(saved.Description.contains('What was tried:'));
    }

    @IsTest
    static void unknownReasonFallsBackToOutOfScope() {
        Contact c = new Contact(LastName = 'Fallback');
        insert c;
        CreateEscalationCaseAction.Request req = new CreateEscalationCaseAction.Request();
        req.contactId = c.Id;
        req.customerIntent = 'x';
        req.attemptSummary = 'y';
        req.handoffReason = 'SOMETHING_ELSE';

        CreateEscalationCaseAction.create(new List<CreateEscalationCaseAction.Request>{ req });
        Assert.areEqual('Agent handoff: OUT_OF_SCOPE', [SELECT Subject FROM Case WHERE ContactId = :c.Id].Subject);
    }
}
```

UNVERIFIED (2026-10-03): the test assumes `Web` is an active `Case.Origin` value, which is a default value in new orgs; adjust if your org removed it.

### 3. The routing: Agent Script escalation

For agents built in Agent Script, escalation uses `@utils.escalate`, which needs an active Omni-Channel connection declared in a `connection messaging` block. Excerpt of the `.agent` file (Agent Script, not YAML):

```text
connection messaging:
    escalation_message: "One moment while I connect you to the next available service representative."
    outbound_route_type: "OmniChannelFlow"
    outbound_route_name: "agent_support_flow"
    adaptive_response_allowed: True

subagent Refund_Processing:
    description: "Handles refund requests for delivered orders."
    reasoning:
        instructions: ->
            | If the refund is above the limit, run {!@actions.create_escalation_case} first,
              then call {!@actions.escalate_to_human}.
        actions:
            create_escalation_case: @actions.Create_Escalation_Case
            escalate_to_human: @utils.escalate
                description: "Call this when the customer needs a service rep"
                available when @variables.in_business_hours
```

The block keys and the `@utils.escalate` form come from the Agentforce Developer Guide (Agent Script Blocks, connection block; Utils reference). `escalate` is a reserved keyword and cannot name a subagent or action. UNVERIFIED (2026-10-03): the exact reference form for a custom Apex action inside `actions:` (`@actions.Create_Escalation_Case` is assumed); generate the bundle from a spec and copy the form it produces.

For agents built in the legacy builder, the standard Escalation topic is the only topic that can invoke the outbound Omni-Channel flow; a custom topic cannot be configured to route to service reps (Generative AI guide, Agent Topic: Escalation). Add `Create_Escalation_Case` to that topic and instruct the agent to run it before escalating.

### 4. Review: the fallback when escalation is unavailable

Retrieve the agent and confirm a fallback exists. Excerpt of a retrieved `Bot`:

```xml
<!-- Excerpt of a retrieved Bot, trimmed to the elements a handoff review reads.
     Element names follow the Metadata API reference for Bot (defaultOutboundFlow: API 65.0 and later). -->
<Bot xmlns="http://soap.sforce.com/2006/04/metadata">
    <agentType>AgentforceServiceAgent</agentType>
    <defaultOutboundFlow>Agent_Fallback_Routing</defaultOutboundFlow>
    <label>Service Agent</label>
    <type>ExternalCopilot</type>
</Bot>
```

`defaultOutboundFlow` "specifies a fallback escalation behavior if the primary agent escalation behavior is not available." `type` = `ExternalCopilot` marks an external-facing agent such as an Agentforce Service agent. Review this element; do not hand-edit retrieved agent metadata to add it, because the Agentforce Developer Guide warns that uploading edited agent metadata can corrupt the org. Set it in the builder and re-retrieve.

The channel also needs an Omni-Channel fallback queue that supports the Messaging Session object; the Enhanced Chat example creates one because "a fallback queue is required so that conversations can escalate to a human service rep."

## package.xml member form

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>CreateEscalationCaseAction</members>
        <members>CreateEscalationCaseActionTest</members>
        <name>ApexClass</name>
    </types>
    <version>66.0</version>
</Package>
```

## Deploy order

1. The Apex class and its test, then grant the agent user Apex class access and create access on Case.
2. The Omni-Channel flow named in `outbound_route_name` (or attached to the Escalation topic), active.
3. The fallback queue for Messaging Session, and the fallback flow if you use `defaultOutboundFlow`.
4. The agent version that references the action and the escalation route; activate it last.

## Verification

- Both test methods pass.
- In preview, a refund above the limit produces a case whose description has the three labelled lines, then the escalation message.
- With no service rep available, the conversation follows the fallback route instead of waiting silently.
