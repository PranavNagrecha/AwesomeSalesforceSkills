# Well-Architected Notes — Agentforce Persona Design

## Relevant Pillars

- **User Experience** — Persona design directly shapes how users experience the agent. An inconsistent or off-brand tone erodes user trust and increases escalation rates. Well-designed persona instructions produce consistent, brand-aligned responses that users find natural and trustworthy.
- **Operational Excellence** — Maintaining a centralized persona in agent-level instructions rather than scattered across subagent instructions (subagents were called topics before April 2026) reduces the authoring and maintenance burden. A single source of truth for tone means brand voice changes require only one update.
- **Reliability** — Contradictory or over-constrained instructions (long must/never/always chains) produce non-deterministic responses that are harder to test and predict. Reliable persona design uses simple, positive behavioral descriptions that the LLM applies consistently.

## Architectural Tradeoffs

- **Rule-based vs adjective-based tone encoding:** Rule lists are intuitive to write, but agents follow absolutes strictly and conflicting rules degrade performance (Generative AI guide). UNVERIFIED (2026-10-03): that rule lists cause reasoning loops. Adjective-based descriptions are less explicit but produce more consistent LLM behavior. Prefer adjectives.
- **Single agent vs multiple agents for multi-persona:** A single agent with persona switching logic is simpler to deploy but unreliable. Multiple agents with dedicated persona per audience is more infrastructure to manage but produces consistent, predictable behavior.
- **Conciseness vs completeness of instructions:** Longer instructions give the LLM more guidance but also more rules to potentially conflict. Start with minimal instructions, as the Generative AI guide recommends. UNVERIFIED (2026-10-03): the earlier ~2,000-character threshold. If instructions grow beyond this, split concerns between agent-level (persona) and subagent-level (task behavior).

## Anti-Patterns

1. **Persona in subagent instructions** — Subagent instructions are scoped to a specific subagent. A persona instruction placed in a subagent (rather than at the agent level) creates inconsistent voice across the agent's conversation surface.
2. **Long modal verb chains as persona encoding**: Using must/never/always lists to encode tone produces stiff, conflicting instructions that agents follow strictly. UNVERIFIED (2026-10-03): the reasoning-loop mechanism. Use voice adjectives and behavioral descriptions instead.
3. **Expecting AI Assist to guarantee runtime consistency**: UNVERIFIED (2026-10-03): AI Assist is described only in a blog source. It is a static analyzer. Runtime consistency requires conversation preview testing with a structured test plan.

## Official Sources Used

Read and checked on 2026-10-03 for this revision:

- Generative AI guide, Spring '26: Update Language Settings (tone options, Casual default), Define System Messages (800 characters, disclose the bot, consent wording), Considerations for Agents (tone and language scope, untranslated system messages, locale variants), Agents Limits (six-turn context for Agentforce (Default)), Best Practices for Writing Topic Instructions (absolutes, minimal instructions, visual order, business rules in actions), Considerations for Custom Actions (output formatting), Troubleshooting Agents: https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/generative_ai.pdf
- Metadata API Developer Guide, Summer '26 (API 67.0): BotVersion (`toneType`, `copilotPrimaryLangauge`, `role` and `company` reserved), Bot (`type`), AiEvaluationDefinition: https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf
- Agentforce Developer Guide, Agent Script Blocks (system block instructions and required welcome and error messages, config role and company, language block): https://developer.salesforce.com/docs/ai/agentforce/guide/ascript-blocks.html
- Agentforce Developer Guide, Agent Metadata V67 and Earlier: A Shallow Dive (authoring bundle files): https://developer.salesforce.com/docs/ai/agentforce/guide/agent-dx-metadata.html
- Agentforce Developer Guide, Use Test Results to Improve Your Agent (semantic `bot_response_rating`, conciseness and coherence metrics): https://developer.salesforce.com/docs/ai/agentforce/guide/testing-api-use-results.html
- Agentforce Developer Guide, Use Metadata to Move an Agent to a New Org (do not edit retrieved agent metadata): https://developer.salesforce.com/docs/ai/agentforce/guide/agent-dx-deploy-metadata.html

### Carried forward from earlier versions (not re-read on 2026-10-03)

These were not re-read for this revision. help.salesforce.com articles do not return their text to a fetch, so claims that rest only on a Help article are marked UNVERIFIED in the skill.

- Salesforce Agentforce Help — Agent Instructions and Tone — https://help.salesforce.com/s/articleView?id=ai.agents_overview.htm&type=5
- Salesforce Developer Blog — Adaptive Response Formats (Oct 2025) — https://developer.salesforce.com/blogs/2025/10/adaptive-response-formats-agentforce
- Salesforce Developer Blog — AI Assist for Agent Instructions (May 2025) — https://developer.salesforce.com/blogs/2025/05/ai-assist-agent-instructions
- Salesforce Architect — Agentic Patterns — https://architect.salesforce.com/docs/architect/agentic-patterns/guide/overview.html
- Agentforce Developer Guide — https://developer.salesforce.com/docs/einstein/genai/guide/agentforce.html
