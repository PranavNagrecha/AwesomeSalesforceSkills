# Well-Architected Notes — Einstein Bots to Agentforce Migration

## Relevant Pillars

- **Reliability** — The migration introduces a new failure mode: LLM planning latency and model availability. A classic bot's scripted dialog steps have predictable execution; an Agentforce agent depends on LLM response time and availability. Migration plans must include fallback handling (graceful degradation to human handoff) and latency SLA validation before go-live.

- **User Experience** — Conversation design changes fundamentally in Agentforce. The LLM can produce varied phrasings and handle natural language turns that a scripted bot cannot. However, the migration to LLM-based routing also introduces the risk of unexpected Topic routing for edge-case inputs. Topic descriptions must be written and tested with real user input samples, not just happy-path phrases.

- **Operational Excellence** — The migration cutover is time-bounded by the Legacy Chat retirement deadline (Feb 14 2026). Operational readiness requires a documented rollback plan (the original bot should remain deployable until the migrated agent is confirmed stable), conversation logging via Enhanced Event Logs, and a handoff latency baseline established before go-live.

- **Security** — Agentforce agents run under a dedicated system user (EinsteinServiceAgent User). The agent's record access at runtime is governed by this user's profile and permission sets — not by the end user's permissions. Any context data passed via `MessagingSession` custom fields must be reviewed for data classification; fields containing PII or sensitive identifiers should be treated accordingly in the Einstein Trust Layer configuration.

## Architectural Tradeoffs

**Full Cutover vs Hybrid Pattern:** A full cutover to Agentforce is simpler to maintain long-term (one system, one authoring surface) but requires re-implementing every dialog as a Topic + Action combination and validating LLM behavior for all conversation paths. The hybrid pattern reduces migration scope and preserves exact-script compliance flows, but introduces operational complexity: two bot systems must be maintained, tested, and deployed together. Teams should choose based on the proportion of deterministic vs open-ended dialogs and the compliance requirements for each.

**"Create AI Agent from Bot" Tool vs Manual Scaffold:** The migration tool reduces scaffolding time for Enhanced Bots but does not reduce validation time. The output is a draft — every Topic description must be rewritten and every Action must be implemented. Teams that treat tool output as production-ready without review will ship an agent with routing gaps. The time savings from the tool are in structure, not in content quality.

**LLM Response Latency vs Scripted Response Time:** Scripted bots are fast because they execute deterministic logic. Agentforce agents are more capable but slower due to LLM planning. This is an architectural tradeoff, not a defect. Teams migrating latency-sensitive flows (authentication steps, time-sensitive disclosures) should evaluate whether those flows belong in Agentforce or should remain in the bot layer under the hybrid pattern.

## Anti-Patterns

1. **Migrating utterance lists as routing logic** — Importing utterances from the old bot and treating them as a trained routing mechanism in Agentforce. Agentforce does not use utterances as a classifier training set. Topic routing accuracy depends entirely on the quality of Topic descriptions. Utterance-heavy Topic instructions reduce, not increase, routing accuracy.

2. **Activating a draft generated agent without reviewing Topics and Actions** — The "Create AI Agent from Bot" tool output is a structural draft. Activating it directly and exposing it to users produces an agent with ambiguous routing descriptions and unimplemented Action placeholders. Always review and rewrite before activation.

3. **Deploying agent metadata without the full bundle** — Omitting `GenAiPlannerBundle` from a deployment silently produces a chatbot (not an agent). The deployment succeeds, the bot responds, but no LLM reasoning occurs. Always deploy the full component set: Bot, BotVersion, GenAiPlannerBundle, GenAiPlugin, GenAiFunction.

## Official Sources Used

- Salesforce Help — Einstein Bots and Agentforce Service Agent comparison
  https://help.salesforce.com/s/articleView?id=sf.bots_service_asa_compare.htm

- Salesforce Help — Create an AI Agent from a Bot (Beta)
  https://help.salesforce.com/s/articleView?id=sf.bots_service_create_agent_from_bot.htm

- Salesforce Help — How Agentforce Service Agent Works
  https://help.salesforce.com/s/articleView?id=sf.bots_service_asa_how_it_works.htm

- Agentforce Developer Guide
  https://developer.salesforce.com/docs/einstein/genai/guide/agentforce.html

- Salesforce Architects — Agentic Patterns
  https://architect.salesforce.com/decision-guides/agentic-patterns

- Salesforce Well-Architected Overview
  https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
