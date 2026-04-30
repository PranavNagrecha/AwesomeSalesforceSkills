# Well-Architected Notes — Agent Action Input Slot Extraction

## Relevant Pillars

- **Reliability** — A correctly-invoked action with the wrong arguments produces wrong-result-with-confidence — the worst outcome an agent can deliver. Slot-extraction discipline (specific descriptions, name-not-ID inputs, normalization) is the cheapest reliability investment in agent design.
- **User Experience** — Users tolerate a clarifying question; they don't tolerate a confidently-wrong result. Per-slot re-prompts and confirmation-on-ambiguity turn slot uncertainty into a productive dialog instead of silent failure.

## Architectural Tradeoffs

- **Description verbosity vs. token cost:** Long descriptions improve extraction but inflate every prompt. Optimize the high-stakes slots; minimal descriptions are fine for low-stakes free-form text.
- **Strict reject vs. graceful coercion:** Rejecting "next Tuesday" forces the user to be explicit; coercing it (with a confirmation) is more forgiving but risks one wrong day. Pick per slot based on cost-of-wrong.
- **Name-then-resolve vs. typed-Id input:** Name-then-resolve adds an Apex SOQL but eliminates ID hallucination. The cost is a few ms; the upside is correctness.

## Anti-Patterns

1. **One-word slot descriptions** — Wastes the description field's leverage; the LLM has no instruction to follow.
2. **Required slots without re-prompt configuration** — Generic re-prompts confuse users; productive dialogs require per-slot questions.
3. **Accepting record IDs from the LLM** — Hallucinated, well-formed, useless. Always take names and resolve server-side.

## Official Sources Used

- Agentforce Developer Guide — https://developer.salesforce.com/docs/einstein/genai/guide/agentforce.html
- Einstein Platform Services — https://developer.salesforce.com/docs/einstein/genai/guide/overview.html
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- Apex `@InvocableMethod` Reference — https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_classes_annotation_InvocableMethod.htm
- Apex `@InvocableVariable` Reference — https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_classes_annotation_InvocableVariable.htm
