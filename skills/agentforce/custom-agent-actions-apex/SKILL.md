---
name: custom-agent-actions-apex
description: "Building custom Apex-based actions for Agentforce agents: designing @InvocableMethod classes for Atlas Reasoning Engine invocation, defining input/output schema, handling errors, and managing security context. NOT for choosing between Apex, Flow, External Service and prompt-template tool shapes — use agentforce/agentforce-tool-use-patterns. NOT for the Apex test class that covers each action branch — use agentforce/agent-action-unit-tests."
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
  - "expose an Apex method as an agent action with the right input and output descriptions"
  - "deploy an Apex-backed agent action as GenAiFunction metadata"
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
version: 1.0.2
author: Pranav Nagrecha
updated: 2026-10-03
---

# Custom Agent Actions Apex

This skill activates when a practitioner needs to build a custom Apex action for an Agentforce agent. The agent decides when and how to call the action from the action's description and its input and output descriptions, which are stored on the `GenAiFunction` metadata and its input/output `schema.json` files. Poor descriptions directly degrade agent reasoning quality and lead to incorrect or missed invocations. When the action is created from an Apex class, those descriptions start from the `@InvocableMethod` and `@InvocableVariable` annotations. UNVERIFIED (2026-10-03): that Agentforce Builder copies the annotation text into the action's descriptions is not stated in the sources read for this revision; check the generated action before relying on it.

---

## Before Starting

Gather this context before working on anything in this domain:

- Determine the agent type: **Employee Agent** runs as the logged-in user (authenticated internal user context), **Service Agent** runs as a designated agent user (typically a restricted integration user). Security context and data visibility differ between the two. The Generative AI guide states that the agent user "determines what your agent can access and do" and that a Service Agent's user gets the Agentforce Service Agent User permission set. UNVERIFIED (2026-10-03): the Employee Agent running-user statement is not in the sources read for this revision.
- Define the action's single responsibility. Each Agentforce action should do one thing well — the agent composes multiple actions to achieve complex goals. A monolithic action that does 5 things is harder for the LLM to invoke correctly.
- Identify whether the action needs an HTTP callout to an external system. If so, set `callout=true` on the annotation. Per the Apex Developer Guide, the modifier "identifies whether the method calls to an external system" and screen flows use it to decide whether to run the action in a new transaction; it does not switch callouts on or off.
- Determine whether the action should be synchronous or needs to chain async work. Agentforce actions execute synchronously during the agent turn — long-running work should be queued and the action should return a tracking ID.

---

## Questions to Ask Before Configuring

| Question | Why it matters | What a good answer adds | What proper configuration adds over just doing it |
|---|---|---|---|
| What one job does the action do, and when should the agent call it? | The agent selects actions from their descriptions; `GenAiFunction.description` is "a description explaining the general purpose and domain of the action" (Metadata API Developer Guide). | A one-sentence "Use when ..." description and a distinct label. | The agent calls the action for the right requests and leaves it alone otherwise. |
| Which inputs come from the user and which outputs should the agent use or show? | The action schema marks inputs with `copilotAction:isUserInput` and outputs with `copilotAction:isDisplayable` and `copilotAction:isUsedByPlanner`; at least one output must be used by the planner "or else the planner returns random responses". | A table of inputs and outputs with those three flags decided. | Answers are grounded in the action's result instead of guessed. |
| Can every input and output be a primitive? | The Generative AI guide says custom actions that reference an Apex class or flow support only primitive data types, and collections aren't supported. | A DTO with String, Boolean, Integer, Decimal, Date fields, plus a JSON string where structure is unavoidable. | The action works in Agentforce, not only in Flow. |
| Whose permissions should the action run with? | The agent user determines what the agent can access; Apex `with sharing` and `WITH USER_MODE` apply that user's sharing and FLS. | The agent user, its permission sets, and any deliberate elevation. | Data exposure is a documented decision, not a side effect of `without sharing`. |
| Does it change data or call out, and should the user confirm first? | `GenAiFunction.isConfirmationRequired` asks for confirmation; DML before a callout in one transaction blocks the callout (Apex Developer Guide, uncommitted work). | A confirm/no-confirm decision and the order of DML and callouts. | Destructive actions pause for the user, and callouts do not fail on uncommitted work. |
| Will the action also be packaged or reused from Flow? | Only one `@InvocableMethod` per class; in managed packages an invocable method cannot be removed in later versions, and only global methods appear in subscriber orgs. | Packaging plan and visibility (public or global). | The action can evolve without a package-version dead end. |

---

## Core Concepts

### @InvocableMethod Annotation and Atlas Reasoning Engine

The `@InvocableMethod` annotation marks an Apex method as callable from Flow, Process Builder, and Agentforce. The Apex Developer Guide says invocable methods "are called natively from REST, Apex, flows, Agentforce agents or AI bots". When an Agentforce agent evaluates what action to take, the Atlas Reasoning Engine reads the action's label and description and the description of every input and output, which for an Apex action are seeded from the method annotation and each `@InvocableVariable` field.

These text values are used verbatim in the LLM's tool-calling context. If the label says "Run Action" and the description is blank, the agent has no information to decide when to use this action. If the description says "Creates a support case in the system when a customer reports a problem", the agent knows exactly when to invoke it.

Rule: every `@InvocableMethod` must have a `label` and a `description`. Every `@InvocableVariable` must have a `label` and a `description` that explains what value to pass.

### Bulk-Safe List-in / List-out Wrapper

The Apex Developer Guide allows at most one input parameter, and when there is one it must be a list (of a primitive, an sObject, or a user-defined type with `@InvocableVariable` fields); a non-void return must also be a list. Inputs and outputs "must match on both the size and the order". For Agentforce, write `List<InputClass>` in and `List<OutputClass>` out, with primitive DTO fields. UNVERIFIED (2026-10-03): earlier versions of this skill said the agent always passes a single-item list; no source read for this revision says so, so keep the method bulk-safe.

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
5. Add `callout=true` if any HTTP callout is needed (it documents the callout and lets screen flows manage the transaction). Use Named Credentials. Do all callouts before any DML in the same transaction.
6. Write an Apex unit test that covers both success and failure paths. Test with a mock callout if the action makes HTTP requests.
7. Deploy and wire the action to the appropriate subagent (called a topic before April 2026) in Agentforce Builder, or deploy the `GenAiFunction` metadata with its input/output schemas (complete set in `references/metadata-examples.md`). Test the agent's ability to invoke the action correctly by running test conversations.

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
2. **`callout=true` is a flow transaction hint, not a callout switch**: Screen flows use it to decide whether to commit and start a new transaction before the action. The "uncommitted work pending" exception comes from DML (or queued async work) before the callout in the same transaction, with or without the modifier. Earlier versions of this skill said omitting it throws a CalloutException even with no prior DML.
3. **Service Agent user context is not the current user** — developers testing in the Developer Console see their own user context. The deployed Service Agent runs as a different, restricted user. SOQL that works in testing may return zero records in production because the service agent user has different sharing or FLS. Always test with a user that matches the service agent's profile.
4. **A parameter, if present, must be a list**: A single-object parameter does not compile, and outputs must line up with inputs by size and order. More traps (planner flags, primitive-only types, text length) are in `references/gotchas.md`.
5. **Throwing exceptions to the agent produces no useful error message** — the agent receives a generic "action failed" signal and cannot tell the user what went wrong. Always catch exceptions, set `success=false`, and populate `errorMessage` with a human-readable string the agent can surface.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Custom action Apex class | @InvocableMethod class with input/output DTOs, security enforcement, error handling |
| Action unit tests | Apex test class covering success and failure paths, mock callout responses if applicable |
| Action wiring documentation | Subagent and action configuration in Agentforce Builder, including which subagents invoke this action |

---

## Related Skills

- agentforce/agentforce-agent-creation — end-to-end agent setup and lifecycle
- agentforce/agent-testing-and-evaluation — testing that the agent invokes actions correctly
- agentforce/einstein-trust-layer — data masking and zero-data retention for callout content
- apex/callouts-and-http-integrations — HTTP callout implementation details
