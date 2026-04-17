# Well-Architected Notes — Agentforce Tool Use Patterns

## Relevant Pillars

- **Reliability** — Tool-per-capability isolation keeps a broken action from cascading through the whole conversation. Soft-error fields keep the agent recoverable when tools fail. Action chaining lets the agent skip steps when data is already available.
- **Performance** — Short return shapes + semantic argument descriptions reduce LLM token usage per turn. Chained actions allow mid-conversation branching without re-running completed work.
- **Security** — Tools are the primary CRUD / FLS / callout surface. Every action that writes or reads sensitive data must enforce sharing explicitly. Named Credentials keep secrets out of prompts.

## Architectural Tradeoffs

### Monolith vs chain

| Approach | Pro | Con |
|---|---|---|
| Monolithic action (one action does N steps) | Single call; simpler to reason about as a transaction | Opaque to user; hard to recover mid-step; LLM has less visibility |
| Chained actions | Transparent; recoverable; user sees progress | More LLM calls; state must pass via session variables |

Rule: chain when the steps involve user-visible decisions (confirm before charge, select from options). Monolith when the steps are internal implementation details (one vendor call that does compound work).

### Apex vs Flow

| When Apex wins | When Flow wins |
|---|---|
| Complex data shaping, strict typing | Admin maintains; visual logic |
| Vendor callouts with custom auth | Simple sObject CRUD |
| Bulk-sensitive operations | Branching orchestration |
| Needs unit test coverage | Rapid iteration |

Rule: start with Flow. Escalate to Apex when Flow limits bind.

### Prompt Template vs retrieval

| Prompt Template | Retrieval |
|---|---|
| Grounded in one or few records | Grounded in a corpus |
| Deterministic inputs | Search over unstructured |
| Best for: draft emails, summaries, explanations of records | Best for: Q&A over KB, policy lookup, product docs |

## Anti-Patterns

1. **Tool-shape mismatch** — Using Apex for simple record CRUD (over-engineered) or Flow for complex transactional work (fragile). Route via the decision tree in SKILL.md.

2. **Ambiguous descriptions** — Two actions that could plausibly answer the same turn. LLM picks inconsistently. Fix: discriminating "USE WHEN / DO NOT use" clauses.

3. **Dumping sObjects in returns** — 200-field Account record in the agent's context. Tokens wasted, response quality degraded. Fix: purpose-built DTOs with 3-6 human-readable fields.

4. **Ungrounded Prompt Templates** — Template with no record inputs is just a hallucinated paragraph. Fix: every template gets at least one record or retrieval result.

5. **No-results hallucination in retrieval** — Agent cites policy that doesn't exist because retrieval returned empty. Fix: explicit `noResults=true` sentinel + prompt handling.

## Official Sources Used

- Salesforce Developer — `@InvocableMethod` Annotation: https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_classes_annotation_InvocableMethod.htm
- Salesforce Help — Agentforce Actions: https://help.salesforce.com/s/articleView?id=sf.copilot_actions.htm
- Salesforce Help — Prompt Builder: https://help.salesforce.com/s/articleView?id=sf.prompt_builder.htm
- Salesforce Developer — Einstein Trust Layer: https://developer.salesforce.com/docs/einstein/genai/guide/trust-layer.html
- Salesforce Architects — AI Architecture Patterns: https://architect.salesforce.com/
