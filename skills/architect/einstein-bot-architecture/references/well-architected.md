# Well-Architected Notes — Einstein Bot Architecture

## Relevant Pillars

- **User Experience** — The bot is the first interaction many customers have with the service organization. Poor dialog design, misrouted intents, and context-less handoffs directly degrade CSAT. Architecture decisions about conversation depth, fallback behavior, and channel-appropriate UI determine whether the bot helps or frustrates.
- **Scalability** — Conversational AI is a scale play. The architecture must handle concurrent session volume without degradation, support incremental intent expansion without retraining the entire taxonomy from scratch, and allow new channels to be added without redesigning dialogs.
- **Reliability**: Bots must handle failure gracefully: unavailable agents, failed API callouts during self-service, unmatched intents, and expired messaging sessions. Every failure path must have a designed exit rather than a dead-end; the platform provides `TransferFailed`, `ErrorHandling`, and `KnowledgeFallback` system dialogs for exactly this. Well-Architected's Resilient guidance asks that agents supporting critical use cases have "viable and relevant workarounds ... that can be switched on with short notice", such as switching to manual handling.
- **Security** — Bot conversations collect PII (names, account numbers, case details). The architecture must ensure that bot variables holding sensitive data are not persisted beyond the session, that pre-chat identity verification gates access to account-specific actions, and that transferred context does not expose data to agents who lack the appropriate profile permissions.
- **Operational Excellence** — A bot that launches and is never tuned degrades over time as customer language shifts and new products are introduced. The architecture must include an analytics feedback loop, a retraining cadence, and clear ownership of intent maintenance.

## Architectural Tradeoffs

**Scripted Dialogs (Einstein Bots) vs. Declarative Topics (Agentforce)**
Scripted dialogs give full control over every conversation step, which is valuable for compliance-sensitive industries where the exact wording matters. Declarative topics are more flexible and handle varied phrasing better, but the LLM can produce unexpected responses if topic descriptions are vague. The tradeoff is control vs. flexibility: choose scripted for regulated processes, declarative for general service.

**Broad Intent Coverage vs. Deep Intent Quality**
Covering more intents increases the theoretical scope of the bot but dilutes training data per intent. Deep coverage of fewer intents produces higher confidence scores and better customer experience. The tradeoff is breadth vs. accuracy: start narrow and expand based on data.

**Full Self-Service vs. Quick Handoff**
Designing the bot to resolve every request autonomously reduces agent workload but increases dialog complexity and maintenance cost. Quick handoff with context preserves simplicity but limits deflection. The tradeoff is deflection rate vs. maintenance cost: use tiered deflection to balance both.

## Anti-Patterns

1. **One giant bot for everything** — Attempting to handle all service scenarios in a single bot with 50+ intents creates an unmaintainable model with low confidence scores. Instead, scope the bot to the top 15-25 intents by volume and explicitly route everything else to agents via a well-designed fallback.

2. **Handoff without context** — Transferring a conversation to an agent without passing collected variables, detected intent, and articles already shown forces the customer to repeat everything. This is worse than not having a bot at all, because the customer already spent time interacting with it. Always map bot variables to transcript fields and build the agent console to surface them.

3. **Launching without analytics targets** — Deploying a bot without defined deflection, containment, and CSAT targets means there is no way to evaluate whether the bot is succeeding. Teams end up making subjective judgments about bot quality instead of data-driven decisions. Set targets before launch and review monthly.

## Official Sources Used

Read for this revision (2026-10-03):

- Metadata API Developer Guide, Version 67.0: https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf. Bot (one active version; `botMlDomain` shared intent set; `contextVariables`; `sessionTimeout`; `defaultOutboundFlow`; `type`; access rules), BotVersion (`intentThreshold` 1 to 5, Support-enabled; `conversationGoals`; `conversationVariables`; `knowledgeActionEnabled`), ConversationContextVariable and ConversationContextVariableMapping, ConversationDefinitionChannelProvider (UI-only messaging channels; `agentRequired`), ConversationSystemDialog types, BotNavigation `TransferToAgent`, ConversationRecordLookup, EmbeddedServiceConfig.
- Salesforce Object Reference, Version 67.0: https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/object_reference.pdf. BotDefinition (Einstein Bots or Agentforce Agents; `Type`, `AgentType`), BotVersion (`Status`, one active), MessagingSession (`ChannelType`, `CaseId`), LiveChatTranscript, ConversationEntry legacy chat maintenance-only note.
- Salesforce Well-Architected: Adaptable > Resilient: https://architect.salesforce.com/docs/architect/well-architected/guide/resilient.html (a direct fetch does not return the guide page; read via Wayback snapshot 2026-06-13). Recovery tactics and switchable workarounds for critical Agentforce use cases; Agentforce testing patterns.
- Salesforce Well-Architected Overview: https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html (Wayback snapshot 2026-06-16). Trusted, Easy, Adaptable framing.

Listed in the original version; Salesforce Help does not fetch, so these were not re-read and no claim in this revision rests on them alone:

- Einstein Bots Overview — https://help.salesforce.com/s/articleView?id=sf.bots_service_intro.htm
- Agentforce Overview — https://help.salesforce.com/s/articleView?id=sf.agentforce_overview.htm
