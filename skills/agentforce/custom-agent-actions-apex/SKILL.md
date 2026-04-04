---
name: custom-agent-actions-apex
description: "Use when building custom Apex-based actions for Agentforce agents: designing @InvocableMethod classes for Atlas Reasoning Engine invocation, defining input/output schema, handling errors, and managing security context. NOT for standard out-of-the-box agent actions, Flow-based actions, or general @InvocableMethod usage in Flow (use flow/* skills)."
category: agentforce
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Reliability
  - Operational Excellence
triggers:
  - "how do I build a custom Apex action for my Agentforce agent"
  - "agent is not invoking my custom action even though it should"
  - "how do I write an @InvocableMethod that an Agentforce agent can call"
  - "agent action keeps failing with an exception instead of returning a useful error"
  - "how do I make a callout from an Agentforce custom action"
tags:
  - agentforce
  - apex-actions
  - invocable-method
  - atlas-reasoning-engine
  - agent-actions
inputs:
  - "Agent type (Employee Agent vs Service Agent)"
  - "Action purpose: what the agent should accomplish with this action"
  - "External system or data source the action needs to call"
  - "Input parameters the agent needs to pass to the action"
  - "Expected output structure the agent needs to reason with"
outputs:
  - "Apex class with @InvocableMethod implementing the custom action"
  - "Input/output DTO classes with descriptive labels"
  - "Error handling strategy returning structured failure responses"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-04
---

# Custom Agent Actions Apex

This skill activates when a practitioner needs to build a custom Apex action for an Agentforce agent. The Atlas Reasoning Engine reads the `label` and `description` on every `@InvocableMethod` and `@InvocableVariable` at runtime to decide when and how to invoke the action — meaning poor descriptions directly degrade agent reasoning quality and lead to incorrect or missed invocations.

---

## Before Starting

Gather this context before working on anything in this domain:

- Determine the agent type: **Employee Agent** runs as the logged-in user (authenticated internal user context), **Service Agent** runs as a designated agent user (typically a restricted integration user). Security context and data visibility differ between the two.
- Define the action's single responsibility. Each Agentforce action should do one thing well — the agent composes multiple actions to achieve complex goals. A monolithic action that does 5 things is harder for the LLM to invoke correctly.
- Identify whether the action needs an HTTP callout to an external system. If so, the method must include `callout=true` in the annotation.
- Determine whether the action should be synchronous or needs to chain async work. Agentforce actions execute synchronously during the agent turn — long-running work should be queued and the action should return a tracking ID.

---

## Core Concepts

### @InvocableMethod Annotation and Atlas Reasoning Engine

The `@InvocableMethod` annotation marks an Apex method as callable from Flow, Process Builder, and Agentforce. When an Agentforce agent evaluates what action to take, the Atlas Reasoning Engine reads the `label` and `description` on both the method annotation and on every `@InvocableVariable` input/output field.

These text values are used verbatim in the LLM's tool-calling context. If the label says "Run Action" and the description is blank, the agent has no information to decide when to use this action. If the description says "Creates a support case in the system when a customer reports a problem", the agent knows exactly when to invoke it.

Rule: every `@InvocableMethod` must have a `label` and a `description`. Every `@InvocableVariable` must have a `label` and a `description` that explains what value to pass.

### Bulk-Safe List-in / List-out Wrapper

All `@InvocableMethod` methods must accept `List<InputClass>` and return `List<OutputClass>`. This is a platform constraint — not optional even for Agentforce. The agent always passes a single-item list, but the bulk wrapper is required for compilation.

```apex
@InvocableMethod(
  label='Create Support Case'
  description='Creates a new Salesforce Case for a customer. Invoke when a customer reports a product issue or service request.'
  callout=false
)
public static List<CaseActionOutput> createCase(List<CaseActionInput> inputs) {
  List<CaseActionOutput> outputs = new List<CaseActionOutput>();
  for (CaseActionInput input : inputs) {
    outputs.add(processRequest(input));
  }
  return outputs;
}
```

### Security Context by Agent Type

**Employee Agent:** The agent runs as the logged-in Salesforce user. All Apex executes with that user's permissions. Standard `with sharing` enforces the user's sharing model. SOQL respects FLS and CRUD.

**Service Agent:** The agent runs as a designated service agent user — typically a restricted integration user configured in the agent's definition. Apex executes in that user's context. If the Apex class is `with sharing`, data access is limited to what the service agent user can see. If `without sharing`, the class can access all records regardless of the user's permissions — use this only when intentional and documented.

Recommendation: use `with sharing` by default. If the service agent user legitimately needs elevated data access, escalate via a dedicated `without sharing` inner utility class with explicit permission checks.

### Structured Output — Return DTOs, Not Exceptions

When an action fails, do NOT throw an unhandled exception. The agent cannot reason about an exception stack trace. Return a structured output that includes a `success` boolean and an `errorMessage` string. The agent can then branch based on the failure response.

```apex
public class CaseActionOutput {
  @InvocableVariable(
    label='Success'
    description='True if the case was created successfully, false if an error occurred.'
  )
  public Boolean success;

  @InvocableVariable(
    label='Case ID'
    description='The Salesforce ID of the created case. Null if success is false.'
  )
  public String caseId;

  @InvocableVariable(
    label='Error Message'
    description='Human-readable error message if success is false. Empty string if success is true.'
  )
  public String errorMessage;
}
```

---

## Common Patterns

### Standard Read Action with Security Enforcement

**When to use:** Action that retrieves data for the agent to reason about.

**How it works:**
1. Define an input DTO with a search parameter (e.g., account name, case number).
2. Use `WITH USER_MODE` in the SOQL query to enforce sharing + FLS in one pass.
3. Return a list of result DTOs with exactly the fields the agent needs — no raw SObjects.

```apex
public class AccountLookupInput {
  @InvocableVariable(
    label='Account Name'
    description='The account name or partial name to search for. Required.'
    required=true
  )
  public String accountName;
}

public class AccountLookupOutput {
  @InvocableVariable(label='Success' description='True if results were found.')
  public Boolean success;
  @InvocableVariable(label='Account Records' description='JSON-serialized list of matching accounts with Id and Name.')
  public String accountsJson;
  @InvocableVariable(label='Error Message' description='Error detail if success is false.')
  public String errorMessage;
}

@InvocableMethod(
  label='Look Up Accounts'
  description='Searches for Salesforce accounts by name. Use when the agent needs to find account information for a customer inquiry.'
)
public static List<AccountLookupOutput> lookupAccounts(List<AccountLookupInput> inputs) {
  List<AccountLookupOutput> outputs = new List<AccountLookupOutput>();
  for (AccountLookupInput inp : inputs) {
    AccountLookupOutput out = new AccountLookupOutput();
    try {
      String searchTerm = '%' + String.escapeSingleQuotes(inp.accountName) + '%';
      List<Account> accts = [SELECT Id, Name FROM Account WHERE Name LIKE :searchTerm WITH USER_MODE LIMIT 10];
      out.success = true;
      out.accountsJson = JSON.serialize(accts);
      out.errorMessage = '';
    } catch (Exception e) {
      out.success = false;
      out.accountsJson = null;
      out.errorMessage = e.getMessage();
    }
    outputs.add(out);
  }
  return outputs;
}
```

### External Callout Action

**When to use:** Action needs to call an external REST API (ERP system, ticketing system, etc.).

**How it works:**
1. Add `callout=true` to the `@InvocableMethod` annotation.
2. Use Named Credentials for authentication — never hardcode credentials.
3. Return a structured output with success/failure and the response data.

```apex
@InvocableMethod(
  label='Get Order Status from ERP'
  description='Retrieves the current status of a customer order from the ERP system by order number. Use when a customer asks about their order status.'
  callout=true
)
public static List<OrderStatusOutput> getOrderStatus(List<OrderStatusInput> inputs) {
  // ... callout implementation
}
```

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Action needs long-running async work | Return a tracking ID immediately, queue work in Queueable | Agent turns are synchronous; blocking for minutes times out |
| Employee Agent data access | `with sharing` class, SOQL `WITH USER_MODE` | User's own permissions define data boundaries |
| Service Agent needs elevated access | `with sharing` default, `without sharing` inner escalation class with explicit check | Prevents accidental over-exposure; documents the escalation |
| Action fails due to validation/business rule | Return `success=false, errorMessage=<reason>` | Agent can surface the error to the user or retry with different inputs |
| Multiple related data operations | One action per operation, agent composes them | Monolithic actions are harder to invoke correctly and harder to test |

---

## Recommended Workflow

1. Define the action's single responsibility in plain English — this becomes the `description` in `@InvocableMethod`. If you cannot describe it in one sentence, split the action.
2. Design the input DTO: identify every parameter the agent needs to pass. Write a `description` for each `@InvocableVariable` that explains what value to provide and in what format.
3. Design the output DTO: always include `success` (Boolean), `errorMessage` (String), and the payload fields. Write descriptions for each output field.
4. Implement the action class with `with sharing`. Use `WITH USER_MODE` in SOQL. Handle all exceptions and return structured error outputs — never throw to the agent.
5. Add `callout=true` if any HTTP callout is needed. Use Named Credentials.
6. Write an Apex unit test that covers both success and failure paths. Test with a mock callout if the action makes HTTP requests.
7. Deploy and wire the action to the appropriate agent topic in Agentforce Builder. Test the agent's ability to invoke the action correctly by running test conversations.

---

## Review Checklist

- [ ] `@InvocableMethod` has both `label` and `description` that clearly explain when to invoke this action
- [ ] Every `@InvocableVariable` on inputs and outputs has a `label` and `description`
- [ ] Method signature uses `List<InputDTO>` in and `List<OutputDTO>` out
- [ ] Output DTO includes `success` (Boolean) and `errorMessage` (String)
- [ ] No unhandled exceptions — all failures return structured error output
- [ ] Class is `with sharing` unless there is an explicit, documented reason for `without sharing`
- [ ] `callout=true` is set on any action that makes HTTP requests
- [ ] Named Credentials used for external authentication — no hardcoded credentials
- [ ] Unit tests cover success and at least one failure path

---

## Salesforce-Specific Gotchas

1. **Missing label/description degrades reasoning** — the Atlas Reasoning Engine uses these strings as the action's "tool card." A blank description means the LLM cannot distinguish this action from others and will either invoke it randomly or never invoke it at all. This is the most common Agentforce action bug.
2. **callout=true omission causes CALLOUT_LOOP exception** — if an action makes an HTTP callout but the annotation omits `callout=true`, the runtime throws a `System.CalloutException: You have uncommitted work pending` error. This happens even if the Apex has no prior DML — the platform checks the annotation before allowing the callout.
3. **Service Agent user context is not the current user** — developers testing in the Developer Console see their own user context. The deployed Service Agent runs as a different, restricted user. SOQL that works in testing may return zero records in production because the service agent user has different sharing or FLS. Always test with a user that matches the service agent's profile.
4. **List-in/List-out is not optional** — even if you are certain only one record will ever be processed, the method signature must be `List<Input>` and `List<Output>`. Changing the signature to a single Input/Output breaks compilation and Flow compatibility simultaneously.
5. **Throwing exceptions to the agent produces no useful error message** — the agent receives a generic "action failed" signal and cannot tell the user what went wrong. Always catch exceptions, set `success=false`, and populate `errorMessage` with a human-readable string the agent can surface.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Custom action Apex class | @InvocableMethod class with input/output DTOs, security enforcement, error handling |
| Action unit tests | Apex test class covering success and failure paths, mock callout responses if applicable |
| Action wiring documentation | Topic and action configuration in Agentforce Builder, including which topics invoke this action |

---

## Related Skills

- agentforce/agentforce-agent-creation — end-to-end agent setup and lifecycle
- agentforce/agent-testing-and-evaluation — testing that the agent invokes actions correctly
- agentforce/einstein-trust-layer — data masking and zero-data retention for callout content
- apex/callouts-and-http-integrations — HTTP callout implementation details
