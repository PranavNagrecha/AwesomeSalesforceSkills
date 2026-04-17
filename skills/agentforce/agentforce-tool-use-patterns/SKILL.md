---
name: agentforce-tool-use-patterns
description: "Pick the right tool shape for each agent action: Apex invocable vs Flow action vs External Service vs Prompt Template vs Data Cloud retrieval. Covers action selection by use case, argument design for LLM clarity, return-shape contracts, error-surfacing, cost implications, and when to chain tools vs keep a single action. NOT for authoring a specific action (use custom-agent-actions-apex). NOT for topic design (use agent-topic-design)."
category: agentforce
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Performance
  - Security
tags:
  - agentforce
  - tool-use
  - agent-actions
  - apex-actions
  - flow-actions
  - external-services
  - prompt-templates
  - routing
triggers:
  - "agentforce tool selection"
  - "apex action vs flow action agent"
  - "external service as agent tool"
  - "prompt template vs action"
  - "agent action chaining"
  - "tool argument design for llm"
inputs:
  - Business capability the agent must invoke
  - Data source (Salesforce record, external API, static config, vector index)
  - Latency budget per turn
  - Security / privacy constraints (PII handling, DLP)
outputs:
  - Tool shape recommendation (Apex invocable / Flow / External Service / Prompt Template / Retrieval)
  - Argument + return-type contract tuned for LLM consumption
  - Error-surfacing plan (soft-error field vs exception vs silent fallback)
  - Chaining topology if multiple tools are needed
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-17
---

# Agentforce Tool Use Patterns

## When to use this skill

Activate when:

- You're deciding how to expose a business capability to an agent (look up an order, calculate shipping, check inventory, cancel a subscription).
- You're seeing the agent pick the wrong tool or pass malformed arguments to a tool it does pick.
- Tool descriptions aren't discriminating well — the LLM confuses two actions with overlapping semantic space.
- You need to decide between one monolithic action and multiple smaller actions.
- You're evaluating whether a workflow should live in Agentforce actions at all vs a separate pre-processing pipeline.

Do NOT use this skill for:
- Authoring the Apex/Flow action itself (use `skills/agentforce/custom-agent-actions-apex`).
- Designing the agent's topic catalog (use `skills/agentforce/agent-topic-design`).
- Prompt Builder template authoring (use `skills/agentforce/prompt-builder-templates`).

## Core concept — five tool shapes, five purposes

Agentforce exposes five abstractions for "things the agent can do". Picking the wrong shape is the most common design error in new deployments.

| Tool shape | Strength | Weakness | Best for |
|---|---|---|---|
| **Apex invocable action** | Full logic power, type safety, transaction control | Development + deployment overhead | Complex business logic, CRUD with FLS, vendor callouts |
| **Flow action** | Admin-maintainable, visual | Limited to Flow elements; no complex data shaping | Simple record CRUD, branching, happy-path orchestration |
| **External Service** | Point-and-click integration of REST APIs | Schema-coupled to the external OpenAPI spec | Exposing a partner REST endpoint to the agent |
| **Prompt Template** | Composable LLM generation with structured inputs | Stochastic — not for deterministic work | Drafting emails, summarizing records, explaining data |
| **Retrieval (Data Cloud / Vector index)** | Grounds responses in curated documents | Quality bound by corpus hygiene | Q&A over KB articles, policy documents, product data |

## Tool selection decision tree

```
Q1. Is the user asking for a FACT already in Salesforce data?
    ├── Yes, simple record lookup          → Flow action (Get Records)
    ├── Yes, complex query / joins / calcs → Apex invocable (bulk-safe)
    └── No                                  → Q2

Q2. Is the user asking for a FACT in an external system?
    ├── Yes, system has OpenAPI spec       → External Service
    ├── Yes, system needs custom auth/logic → Apex with Named Credential
    └── No                                  → Q3

Q3. Is the user asking a FACT in unstructured content (docs, KB)?
    ├── Yes, on-demand grounding           → Retrieval (Data Cloud vector search)
    └── No                                  → Q4

Q4. Is the user asking for GENERATED CONTENT (summary, draft, explanation)?
    ├── Yes, based on a record              → Prompt Template (grounded)
    ├── Yes, freeform creative             → Prompt Template (open)
    └── No                                  → Q5

Q5. Is the user asking the agent to TAKE an action (create, update, cancel)?
    ├── Simple 1-object write              → Flow action
    ├── Multi-step with validation         → Apex invocable (transactional)
    ├── External system write              → External Service or Apex callout
    └── Requires human approval first      → Flow + Approval Process
```

## Recommended Workflow

1. **Classify each capability by data direction:** reading Salesforce, reading external, reading unstructured, generating content, writing Salesforce, writing external.
2. **Route each capability through the decision tree** above.
3. **For each tool, design the LLM-facing contract:** the action name, description, input variable descriptions, output variable descriptions. These are what the model sees and uses to decide WHICH tool + WHAT arguments.
4. **Write the description as if for a new engineer on Monday morning.** The LLM behaves like that engineer — if the description is ambiguous, the model picks wrong.
5. **Design return shapes that are short.** Every token the tool returns is a token the LLM has to process. Return only what the user needs; never dump the whole sObject.
6. **Plan for tool failure.** Soft error (field on return) vs exception (fault path) — see `agentforce-multi-turn-patterns` error handling.
7. **Decide on chaining.** One big action or several small ones? Prefer small + chained; LLMs compose them better than they understand monoliths.
8. **Add eval cases** that exercise each tool in isolation + in natural combinations.

## Key patterns

### Pattern 1 — LLM-friendly argument design

Bad (the LLM has to guess):
```
@InvocableMethod(label='LookupOrder')
public class Request {
    @InvocableVariable
    public String id;        // Which id? Order number? Salesforce Id? External?
}
```

Good:
```
@InvocableMethod(
    label='Look Up Order',
    description='Look up an order by its customer-facing order number (e.g. "A7842"). Does NOT accept Salesforce record IDs.'
)
public class Request {
    @InvocableVariable(
        required=true
        label='Order Number'
        description='Customer-facing order number exactly as printed on the receipt or email. Format: letter followed by 4 digits (e.g. A7842). Do not include the "#" prefix.'
    )
    public String orderNumber;
}
```

Why: the LLM has strong priors against ambiguous names like "id". Specific, example-bearing descriptions cut argument-malformation rates dramatically.

### Pattern 2 — Short, shaped returns

The agent's return should fit on one LLM turn. A 500-field sObject payload wastes tokens and degrades downstream reasoning.

```apex
public class OrderResult {
    @InvocableVariable(label='Order Number')
    public String orderNumber;

    @InvocableVariable(label='Status (display text)')
    public String statusDisplay;  // "Processing", not "PROC_INT_2"

    @InvocableVariable(label='Total (formatted)')
    public String totalDisplay;   // "$149.99", not 149.99

    @InvocableVariable(label='Items (plain-language summary)')
    public String itemsSummary;   // "2× Blue Scarf, 1× Hat"

    @InvocableVariable(label='Error (if lookup failed)')
    public String error;
}
```

Why: the agent's next turn will include the entire return in its prompt. Human-readable strings perform better in user-facing generation than raw codes.

### Pattern 3 — Action chaining

Instead of one monolithic `Cancel_And_Refund_Order` action, split:
1. `Look_Up_Order` → returns order + user-confirmation-required flag.
2. `Cancel_Order` → takes orderNumber, returns cancellation confirmation.
3. `Issue_Refund` → takes orderNumber + amount, returns refund ID.

Agent composes: look up → confirm with user → cancel → refund. Each step is testable independently; the agent can recover mid-chain if one step fails.

### Pattern 4 — Prompt Template as a grounded generator

Use case: draft a response to a support case.

```
Prompt Template: "Draft Case Reply"
  Inputs: {caseId} (Record: Case)
  Grounding:
    - Case.Description
    - Case.Account.KnownIssues
    - Related Knowledge__kav articles (retrieval)
  Output: 2-3 paragraph draft reply, tone = professional friendly
```

The template's `Inputs` field pulls fully-populated records from Salesforce at runtime, keeping the generation grounded in real data instead of free-form hallucination.

### Pattern 5 — Retrieval as a tool

Use case: answer policy questions over 500 KB articles.

- Index articles into Data Cloud with a vector embedding.
- Expose as an action: `Look_Up_Policy` (query string in, top-3 article excerpts out).
- Agent composes: on a policy question, call retrieval, then answer using returned excerpts.

The agent's prompt enforces: "Only cite information from the retrieved excerpts. If the excerpts don't answer the question, say so."

## Bulk safety

- Flow actions for agents typically execute for one conversation at a time; the bulk concern is about the underlying Flow being bulk-safe when called from other contexts.
- Apex invocables exposed as agent actions MUST still follow the bulk contract (see `skills/flow/flow-invocable-from-apex`). Single-list inputs, single-list outputs, bulk query + bulk DML.
- Retrieval tools should cache embeddings at index time; per-query cost should be bounded to top-K retrieval + summarization, never re-embed.

## Error handling

Each tool shape has a different error-surfacing model:

- **Apex invocable:** populate an `error` output field for soft errors; throw `AuraHandledException` for system errors.
- **Flow action:** wire a fault path that returns a structured error; never silently complete.
- **External Service:** the platform exposes 4xx/5xx to the agent as action failures; design the action-level error-message text (not the raw API error).
- **Prompt Template:** has no error concept; design the prompt with "If the data is insufficient, reply with 'I don't have enough information to answer.'"
- **Retrieval:** if zero results, return an explicit "no-results" marker instead of empty list; the agent should recognize and escalate.

## Well-Architected mapping

- **Reliability** — tool-per-capability isolates failures: one broken action doesn't crash the whole conversation. Error-surfacing contract discipline keeps error messages user-safe.
- **Performance** — short return shapes cut LLM token usage; action chaining lets the model skip steps when data is already in session. Monolithic actions force the model to always do all work.
- **Security** — tools are the primary CRUD / FLS / callout surface. Every tool must be sharing-audited. Named Credentials keep secrets out of prompts.

## Gotchas

See `references/gotchas.md`.

## Testing

Per-tool unit tests (Apex invocable bulk cases) + conversation-level evals that exercise combinations. See `skills/agentforce/agentforce-eval-harness`.

## Official Sources Used

- Salesforce Developer — Invocable Actions for Agents: https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_classes_annotation_InvocableMethod.htm
- Salesforce Help — Agentforce Actions: https://help.salesforce.com/s/articleView?id=sf.copilot_actions.htm
- Salesforce Help — Prompt Builder: https://help.salesforce.com/s/articleView?id=sf.prompt_builder.htm
- Salesforce Help — External Services for Agents: https://help.salesforce.com/s/articleView?id=sf.external_services.htm
- Salesforce Architects — Grounding Agents with Enterprise Data: https://architect.salesforce.com/
