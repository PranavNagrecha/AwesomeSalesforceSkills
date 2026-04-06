# Well-Architected Notes — Agentforce Persona Design

## Relevant Pillars

- **User Experience** — Persona design directly shapes how users experience the agent. An inconsistent or off-brand tone erodes user trust and increases escalation rates. Well-designed persona instructions produce consistent, brand-aligned responses that users find natural and trustworthy.
- **Operational Excellence** — Maintaining a centralized persona in agent-level instructions rather than scattered across topic instructions reduces the authoring and maintenance burden. A single source of truth for tone means brand voice changes require only one update.
- **Reliability** — Contradictory or over-constrained instructions (long must/never/always chains) produce non-deterministic responses that are harder to test and predict. Reliable persona design uses simple, positive behavioral descriptions that the LLM applies consistently.

## Architectural Tradeoffs

- **Rule-based vs adjective-based tone encoding:** Rule lists are intuitive to write but cause reasoning loops and inconsistency. Adjective-based descriptions are less explicit but produce more consistent LLM behavior. Prefer adjectives.
- **Single agent vs multiple agents for multi-persona:** A single agent with persona switching logic is simpler to deploy but unreliable. Multiple agents with dedicated persona per audience is more infrastructure to manage but produces consistent, predictable behavior.
- **Conciseness vs completeness of instructions:** Longer instructions give the LLM more guidance but also more rules to potentially conflict. Keep instruction text under ~2000 characters. If instructions grow beyond this, split concerns between agent-level (persona) and topic-level (task behavior).

## Anti-Patterns

1. **Persona in topic instructions** — Topic instructions are scoped to a specific topic. A persona instruction placed in a topic (rather than at the agent level) creates inconsistent voice across the agent's conversation surface.
2. **Long modal verb chains as persona encoding** — Using must/never/always lists to encode tone causes reasoning loops. Use voice adjectives and behavioral descriptions instead.
3. **Expecting AI Assist to guarantee runtime consistency** — AI Assist is a static analyzer. Runtime consistency requires conversation preview testing with a structured test plan.

## Official Sources Used

- Salesforce Agentforce Help — Agent Instructions and Tone — https://help.salesforce.com/s/articleView?id=ai.agents_overview.htm&type=5
- Salesforce Developer Blog — Adaptive Response Formats (Oct 2025) — https://developer.salesforce.com/blogs/2025/10/adaptive-response-formats-agentforce
- Salesforce Developer Blog — AI Assist for Agent Instructions (May 2025) — https://developer.salesforce.com/blogs/2025/05/ai-assist-agent-instructions
- Salesforce Architect — Agentic Patterns — https://architect.salesforce.com/docs/architect/agentic-patterns/guide/overview.html
- Agentforce Developer Guide — https://developer.salesforce.com/docs/einstein/genai/guide/agentforce.html
