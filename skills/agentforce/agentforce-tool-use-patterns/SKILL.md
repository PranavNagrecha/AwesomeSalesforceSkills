---
name: agentforce-tool-use-patterns
description: "Pick the right tool shape for each agent action: Apex invocable vs Flow action vs External Service vs Prompt Template vs Data Cloud retrieval. Covers action selection by use case, argument design for LLM clarity, return-shape contracts, error-surfacing, cost implications, and when to chain tools vs keep a single action. NOT for designing or reviewing an action whose shape is already settled — naming, confirmation, error behavior — use agentforce/agent-actions. NOT for writing the Apex class itself — use agentforce/custom-agent-actions-apex."
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
  - "choose between a flow action and an apex action for my agent"
  - "design the input and output schema for an agent action"
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
version: 1.0.2
author: Pranav Nagrecha
updated: 2026-10-03
---

# Agentforce Tool Use Patterns

## Questions to Ask Before Configuring

Ask these before choosing a tool shape. Each one traces to a gotcha in `references/gotchas.md`.

| Question | Why it matters | What a good answer adds | What proper configuration adds over just doing it |
|---|---|---|---|
| "Is this capability deterministic (look up, write, calculate) or generative (draft, summarize)?" | Apex, flows and standard invocable actions run without an LLM call; prompt templates need one (Gotcha 13) | A tool shape per capability, chosen by the decision tree below | Lower consumption and latency, and no generated text where a fact is needed |
| "What exactly goes in and comes out, field by field?" | Custom actions on Apex or flows take primitive types only; text fields stop at 250 characters (Gotchas 12, 14) | A request and result contract with one primitive per input and short display strings per output | An action the planner can fill reliably, instead of one that needs collection or sObject inputs it cannot pass |
| "What should the agent say or do with each output?" | Output instructions are read by the planner, and at least one output must be used by it (Gotcha 3) | An instruction per output and a "Show in conversation" decision per field | Answers built from the right fields, not random responses |
| "Which step must run before which?" | Dependent actions need explicit ordering in the action or subagent instructions (see `references/metadata-examples.md`) | A chain such as look up, confirm, write, with the order stated by API name | A plan that cannot write before it has read |
| "How long can the slowest step take, and which channel serves the agent?" | Agent API calls time out at 120 seconds (Gotcha 16) | A latency budget per tool and an async path for slow work | No HTTP 500 for a customer whose request was fine |
| "Is the reference action shared with a screen flow or a managed package?" | `callout=true` and package rules change what is safe (Gotchas 2, 10) | The reuse map for each invocable | One invocable that is safe in every context that calls it |

## Core concept — five tool shapes, five purposes

Agentforce exposes five abstractions for "things the agent can do". Picking the wrong shape is the most common design error in new deployments.

| Tool shape | Strength | Weakness | Best for |
|---|---|---|---|
| **Apex invocable action** | Full logic power, type safety, transaction control | Development + deployment overhead | Complex business logic, CRUD with FLS, vendor callouts |
| **Flow action** | Admin-maintainable, visual | Limited to Flow elements; no complex data shaping | Simple record CRUD, branching, happy-path orchestration |
| **External Service** | Point-and-click integration of REST APIs | Schema-coupled to the external OpenAPI spec | Exposing a partner REST endpoint to the agent |
| **Prompt Template** | Composable LLM generation with structured inputs | Stochastic — not for deterministic work | Drafting emails, summarizing records, explaining data |
| **Retrieval (Data Cloud / Vector index)** | Grounds responses in curated documents | Quality bound by corpus hygiene | Q&A over KB articles, policy documents, product data |


### How each shape lands in metadata

Every agent action is a `GenAiFunction` whose `invocationTargetType` names the shape: `apex`, `flow`, `generatePromptResponse` (prompt template), `externalService`, `retriever`, `standardInvocableAction`, `namedQuery`, `auraEnabled`, `api`, `mcpTool`, `quickAction` and a few others (Metadata API reference). Inputs and outputs live in `input/schema.json` and `output/schema.json` beside the component, and those schemas are what the planner reads. `references/metadata-examples.md` shows an Apex tool end to end, and `scripts/check_agentforce_tool_use_patterns.py` lints the contract.

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
3. **Design the LLM-facing contract for each tool.**
   - The action name, description, input variable descriptions, output variable descriptions. These are what the model sees and uses to decide WHICH tool + WHAT arguments.
   - Write the description as if for a new engineer on Monday morning. The LLM behaves like that engineer — if the description is ambiguous, the model picks wrong.
   - Design return shapes that are short. Every token the tool returns is a token the LLM has to process. Return only what the user needs; never dump the whole sObject.
4. **Decide granularity and failure behavior.**
   - Chaining: one big action or several small ones? Prefer small + chained; LLMs compose them better than they understand monoliths.
   - Tool failure: soft error (field on return) vs exception (fault path) — see `agentforce-multi-turn-patterns` error handling.
5. **Lint the contract.** Run `python3 scripts/check_agentforce_tool_use_patterns.py --manifest-dir force-app/main/default` and fix every ERROR (list parameter, schema fields, planner-visible output) before review.
6. **Add eval cases** that exercise each tool in isolation + in natural combinations.

## Key patterns

### Pattern 1 — LLM-friendly argument design

Bad (the LLM has to guess):
```apex
// Excerpt: the request class and the method signature only.
public class Request {
    @InvocableVariable
    public String id;        // Which id? Order number? Salesforce Id? External?
}

@InvocableMethod(label='LookupOrder')
public static List<Result> lookUp(List<Request> requests) { /* ... */ }
```

Good:
```apex
// Excerpt: the request class and the method signature only.
public class Request {
    @InvocableVariable(
        required=true
        label='Order Number'
        description='Customer-facing order number exactly as printed on the receipt or email. Format: letter followed by 4 digits, for example A7842. Take it from the user message. Do not include the "#" prefix.'
    )
    public String orderNumber;
}

@InvocableMethod(
    label='Look Up Order'
    description='Look up an order by its customer-facing order number. Does NOT accept Salesforce record IDs.'
)
public static List<Result> lookUp(List<Request> requests) { /* ... */ }
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

- Create a data library over the articles. The library creates the data stream, search index and retriever, and the standard Answer Questions with Knowledge action uses it (Generative AI guide, Einstein Data Library).
- For a custom shape, expose a retriever-backed action (`invocationTargetType` = `retriever`) or a prompt template grounded on the retriever.
- Agent composes: on a policy question, call retrieval, then answer using returned excerpts.

The agent's prompt enforces: "Only cite information from the retrieved excerpts. If the excerpts don't answer the question, say so."

## Bulk safety

- Flow actions for agents typically execute for one conversation at a time; the bulk concern is about the underlying Flow being bulk-safe when called from other contexts.
- Apex invocables exposed as agent actions MUST still follow the bulk contract (see `skills/flow/flow-invocable-from-apex`). Single-list inputs, single-list outputs, bulk query + bulk DML, and outputs that match inputs in size and order.
- Retrieval tools should cache embeddings at index time; per-query cost should be bounded to top-K retrieval + summarization, never re-embed.

## Error handling

Each tool shape has a different error-surfacing model:

- **Apex invocable:** populate an `error` output field and return one result per input, in order, even when some inputs fail (Apex Developer Guide, InvocableMethod Annotation). UNVERIFIED (2026-10-03): the earlier advice to throw `AuraHandledException` for system errors; no source read describes how an agent surfaces a thrown exception, so prefer the result field.
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

See `references/well-architected.md` for the sources read for this revision.
