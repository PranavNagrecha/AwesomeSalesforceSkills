# Agentforce Topic Template

A Topic is the discoverable unit of an Agentforce agent. When the user says
something the router thinks matches this topic, the agent enters it and has
access to the actions listed below.

Copy this as the topic's Instructions / Description and fill in the sections.

---

## Topic name

`<Verb_Noun>` — short, action-oriented (e.g. `Create_Case`, `Summarize_Account`).

## When to activate (classifier)

Describe — in natural language, as the user would say it — the **3–8 canonical
trigger phrases**. The router uses these verbatim for training.

```
- "Create a case for Acme about a billing issue"
- "Open a new support ticket for this account"
- "Log a case and assign it to the billing queue"
```

## When NOT to activate (anti-patterns)

Listing NOT-scope prevents false activations. Be explicit.

```
- NOT for updating an existing case — use the Update_Case topic.
- NOT for closing a case — use Close_Case.
- NOT for questions about an existing case — use Summarize_Case.
```

## Actions available in this topic

| Action (Apex class) | What it does | Required inputs |
|---|---|---|
| `CreateCaseAction` | Creates a Case and assigns to a queue | accountId, subject, origin |
| `GetCaseQueuesAction` | Returns available queues for the user | — |
| `NotifyOwnerAction` | Sends a Chatter notification to the owner | caseId, message |

## Instructions to the agent (system prompt fragment)

```
When activated on this topic:

1. Confirm the Account with the user if not already in context.
2. Ask ONLY for fields you cannot derive (Subject, Priority).
3. Never invent Case Record Type — call GetCaseQueuesAction to discover valid options.
4. After creating the case, quote the case number to the user (format: "00012345").
5. If CreateCaseAction returns success=false, present the error verbatim — do not invent a
   retry strategy unless the user explicitly asks.
```

## Guardrails

- Require confirmation before any DML that creates or modifies **more than 1**
  record at a time.
- Never call an action that reads PII fields (SSN, DOB, phone) unless the user
  has explicitly named the field.
- Honor the Einstein Trust Layer masking configuration — do not echo masked
  values back to the model.

## Test utterances (for agent evaluation)

```
✓ "Create a case for Acme Corp about their failed invoice on March 12"
✓ "Open a P1 ticket for this account — website is down"
✗ "Close this case"  → should route to Close_Case, NOT this topic
✗ "What's the status of case 00012345?" → should route to Summarize_Case
```
