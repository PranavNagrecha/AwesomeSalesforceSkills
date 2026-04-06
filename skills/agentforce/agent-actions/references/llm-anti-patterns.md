# LLM Anti-Patterns — Agent Actions

Common mistakes AI coding assistants make when generating or advising on Agentforce agent actions.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Designing Actions Without Confirmation Steps for Destructive Operations

**What the LLM generates:** An agent action that directly updates, deletes, or creates records without requiring user confirmation, treating every action as safe to auto-execute.

**Why it happens:** LLMs focus on completing the task flow and do not distinguish between read-only actions and destructive (write, delete, status-change) actions. The Agentforce confirmation requirement pattern is specific to the Agentforce runtime and not commonly documented.

**Correct pattern:**

```text
Action confirmation classification:

Safe to auto-execute (no confirmation needed):
- Read-only queries (get account details, list opportunities)
- Informational summaries (summarize case history)

Requires confirmation before execution:
- Record creation (create case, create opportunity)
- Record update (change stage, update owner)
- Record deletion (delete draft quote)
- Outbound communication (send email, post to Chatter)
- Financial operations (apply discount, adjust price)

Implementation:
- Set "Require Confirmation" = true on the action definition
- Include a human-readable summary of what will change
- Show the key field values that will be written
- Allow the user to cancel before execution
```

**Detection hint:** Flag agent actions that create, update, or delete records without the confirmation requirement enabled. Check for outbound communication actions (email, Chatter) missing confirmation.

---

## Anti-Pattern 2: Creating Monolithic Actions Instead of Composable Single-Purpose Actions

**What the LLM generates:** A single Apex invocable action or Flow that handles the entire business process (look up account, check open cases, create a new case, assign it, send notification) instead of breaking it into discrete, reusable actions.

**Why it happens:** LLMs optimize for fewer moving parts. A single action that does everything is simpler to describe. However, the Agentforce planner works best when actions are small, well-named, and composable — the LLM planner can chain them in the right order based on the conversation.

**Correct pattern:**

```text
Composable action design:

Monolithic (anti-pattern):
  "HandleCustomerIssue" — looks up account, checks cases,
  creates case, assigns, sends email — all in one action.
  The agent cannot skip steps or reorder.

Composable (recommended):
  1. "Get Account Details" — input: account name → output: account record
  2. "List Open Cases" — input: account ID → output: case list
  3. "Create Case" — input: account ID, subject, description → output: case ID
  4. "Assign Case to Queue" — input: case ID, queue name → output: confirmation
  5. "Send Case Confirmation Email" — input: case ID → output: confirmation

Benefits:
- Agent can skip "List Open Cases" if user already provided context
- Each action is independently testable
- Actions are reusable across multiple topics
- Agent planner can reason about each step
```

**Detection hint:** Flag actions with more than 3 distinct data operations (query + DML + callout). Check for actions whose names suggest multiple verbs ("CreateAndAssignCase", "LookupAndUpdate").

---

## Anti-Pattern 3: Using Vague or Generic Action Names and Descriptions

**What the LLM generates:** Actions named "ProcessData", "HandleRequest", or "DoAction" with descriptions like "This action processes the request" — which give the Agentforce planner no useful signal about when to invoke the action.

**Why it happens:** LLMs default to abstract naming. In traditional development, method names are for humans. In Agentforce, the action name and description are consumed by the LLM planner to decide WHICH action to invoke. Vague names cause the planner to select the wrong action or fail to select any.

**Correct pattern:**

```text
Action naming for Agentforce planner consumption:

Bad: "ProcessRequest"
Good: "Create Support Case for Customer"

Bad: "GetData"
Good: "Look Up Account by Name or Account Number"

Action description best practices:
- Start with a verb: "Creates...", "Retrieves...", "Updates..."
- State the object: "...a Case record", "...the Account"
- Include when to use: "Use when the customer wants to report a new issue"
- Include when NOT to use: "Do not use for existing case updates"
- Mention key inputs: "Requires customer name and issue description"

The description is the planner's primary signal for action selection.
A 2-sentence description is better than a 2-word description.
```

**Detection hint:** Flag actions with single-word names or descriptions shorter than 10 words. Check for action names that do not include the target object or verb.

---

## Anti-Pattern 4: Not Defining Structured Input and Output Schemas

**What the LLM generates:** Actions with loosely typed inputs (a single String parameter containing free-text JSON, or multiple optional parameters with no validation) and unstructured output (raw JSON or a generic String response).

**Why it happens:** Flexible inputs are easier to code. LLMs do not consider that the Agentforce planner must map conversational context to action inputs. Strongly typed, well-labeled parameters with clear descriptions help the planner extract and assign values correctly.

**Correct pattern:**

```text
Input schema design:

Bad:
  @InvocableVariable String requestPayload  // free-text JSON

Good:
  @InvocableVariable(label='Customer Name' description='Full name of the customer' required=true)
  String customerName;

  @InvocableVariable(label='Issue Category' description='Category: Billing, Technical, or General')
  String issueCategory;

Output schema design:

Bad:
  return JSON.serialize(result);  // raw JSON string

Good:
  public class ActionOutput {
    @InvocableVariable(label='Case Number' description='The newly created case number')
    public String caseNumber;

    @InvocableVariable(label='Case ID' description='18-character Salesforce ID')
    public String caseId;
  }

Rules:
- Use required=true for parameters the action cannot function without
- Use description on every parameter (planner reads these)
- Return structured output so the planner can use specific fields
- Limit inputs to 5-7 parameters maximum per action
```

**Detection hint:** Flag actions with a single String input for JSON payloads. Check for @InvocableVariable fields missing label or description attributes. Flag actions returning unstructured String output.

---

## Anti-Pattern 5: Not Handling Errors Gracefully in Agent-Facing Actions

**What the LLM generates:** Actions that throw unhandled exceptions or return raw Salesforce error messages (e.g., "FIELD_CUSTOM_VALIDATION_EXCEPTION: Discount cannot exceed 40%") directly to the agent conversation, exposing internal implementation details to the end user.

**Why it happens:** Standard Apex error handling surfaces DML exceptions or callout failures. In a non-agent context, these are displayed in a toast or logged. In the Agentforce context, the error text becomes part of the conversation, and the agent may parrot the raw exception to the user.

**Correct pattern:**

```text
Agent-friendly error handling:

Bad (raw exception surfaces to conversation):
  insert newCase;  // DMLException goes to agent as-is

Good (catch and return user-friendly message):
  public class ActionOutput {
    @InvocableVariable public Boolean success;
    @InvocableVariable public String userMessage;
    @InvocableVariable public String errorCode;
  }

  try {
    insert newCase;
    output.success = true;
    output.userMessage = 'Case ' + newCase.CaseNumber + ' created.';
  } catch (DmlException e) {
    output.success = false;
    output.userMessage = 'I was unable to create the case. '
      + 'Please verify the information and try again.';
    output.errorCode = 'CASE_CREATE_FAILED';
    // Log the real exception for admin debugging
    Logger.error('Agent action DML failure', e);
  }

Error handling rules:
- Never expose field API names, exception types, or stack traces
- Return a success/failure flag so the planner can branch
- Provide a user-friendly message the agent can relay
- Log the technical error separately for admin investigation
```

**Detection hint:** Flag agent-facing Apex actions that do not wrap DML or callout operations in try-catch blocks. Check for actions that surface raw exception messages without translation.

---
