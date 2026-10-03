# Well-Architected Notes — Agent Topic Design

## Relevant Pillars

- **User Experience** - well-bounded subagents (called topics before April 2026) make the agent feel focused instead of random.
- **Reliability** - cleaner subagent routing reduces wrong-action and wrong-answer behavior.
- **Operational Excellence** - smaller, explicit subagent sets are easier to review and evolve safely.

## Architectural Tradeoffs

- **Few broad subagents vs many narrow subagents:** broad subagents are easier to list, but often too fuzzy; narrow subagents are safer, but can become noisy if there are too many.
- **Flat subagent list vs topic selector:** a flat list is simpler at first, but selectors help when the domain becomes too large.
- **Optimistic in-subagent handling vs explicit handoff:** keeping the agent in control feels smoother, but explicit handoff is safer once the subagent boundary is crossed.

## Anti-Patterns

1. **Department-style subagents** - these are not sharp enough to guide reliable routing.
2. **No out-of-scope behavior** - the agent keeps operating beyond its real boundary.
3. **Subagent sprawl with overlapping capabilities** - review and maintenance become unreliable.

## Official Sources Used

- Quickstart Your Einstein Generative AI Solution (Generative AI guide, Spring '26): https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/generative_ai.pdf. Sections used: What are Agents? (topic classification by name and classification description), Agents Limits (15 actions per topic, 20 agents), Parts of a Topic, Best Practices for Writing Topic Instructions, Add an Action to a Topic, Considerations for Agent Conversations (one intent per utterance), Set up Einstein Trust Layer (org-level settings).
- Agentforce Developer Guide, Get Started with Agent Script (April 2026 rename to subagents): https://developer.salesforce.com/docs/ai/agentforce/guide/agent-script.html
- Agentforce Developer Guide, Agent Script Pattern: Agent Router: https://developer.salesforce.com/docs/ai/agentforce/guide/ascript-patterns-topic-selector.html
- Agentforce Developer Guide, Agent Script Pattern: Subagent Transitions: https://developer.salesforce.com/docs/ai/agentforce/guide/ascript-patterns-transitions.html
- Agentforce Developer Guide, Agent Script Reference: Utils (`transition to`, `escalate`): https://developer.salesforce.com/docs/ai/agentforce/guide/ascript-ref-utils.html
- Agentforce Developer Guide, Agent Script Blocks (runtime citation and groundedness): https://developer.salesforce.com/docs/ai/agentforce/guide/ascript-blocks.html
- Agentforce Developer Guide, Agent Metadata (GenAiPlugin represents a subagent): https://developer.salesforce.com/docs/ai/agentforce/guide/agent-dx-metadata.html
- Agentforce Developer Guide, Build Tests in Metadata API (AiEvaluationDefinition): https://developer.salesforce.com/docs/ai/agentforce/guide/testing-api-build-tests.html
- Metadata API Developer Guide (Spring '26), GenAiPlugin, GenAiPluginInstructionDef, AiPluginUtteranceDef, GenAiPlannerBundle, AiAuthoringBundle: https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf

Carried from earlier revisions (not re-read on 2026-10-03):

- Agentforce Developer Guide (older einstein/genai path; returned HTTP 404 on 2026-10-03, superseded by the developer.salesforce.com/docs/ai/agentforce/guide/ pages above): https://developer.salesforce.com/docs/einstein/genai/guide/agentforce.html
- Einstein Platform Services - https://developer.salesforce.com/docs/einstein/genai/guide/overview.html
- Salesforce Well-Architected Overview - https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
