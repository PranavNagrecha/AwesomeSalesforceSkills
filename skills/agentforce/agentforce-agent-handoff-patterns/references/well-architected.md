# Well-Architected Notes — Agentforce Agent Handoff

## Relevant Pillars

- **User Experience** — explicit transfer + expected-wait messaging beats silent queueing.
- **Reliability** — loops are the top failure mode; confidence-triggered escalation prevents them.
- **Operational Excellence** — structured context packages reduce human-agent ramp time.

## Architectural Tradeoffs

- **Warm vs cold handoff:** warm (agent summary + context) costs more per transfer but yields faster resolution; cold is cheap but slower.
- **Queue vs callback:** queueing is immediate but can strand users; callback respects wait-time expectations but has its own ops tail.
- **Hand-back vs one-way:** hand-back enables hybrid models but requires resumption scaffolding.

## Anti-Patterns

1. Raw transcript dumps into case descriptions.
2. No confidence-triggered escalation, leading to loops.
3. Handoff without a user message.

## Official Sources Used

Read and checked on 2026-10-03 for this revision:

- Generative AI guide, Spring '26: Agent Topic: Escalation (only the standard Escalation topic routes to reps; default escalates on request; avoid standard actions), Considerations for Agents (only Agentforce Service Agent connects to enhanced Messaging and Bring Your Own Channel), Activate or Deactivate Your Agent: https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/generative_ai.pdf
- Metadata API Developer Guide, Summer '26 (API 67.0): Bot (`defaultOutboundFlow` from API 65.0, `type`, `agentType`), GenAiPlugin and GenAiPlannerBundle (`canEscalate`): https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf
- Agentforce Developer Guide, Agent Script Reference: Utils (`@utils.escalate`, reserved keyword, one-way transitions, restart on return, `@utils.end_session`): https://developer.salesforce.com/docs/ai/agentforce/guide/ascript-ref-utils.html
- Agentforce Developer Guide, Agent Script Blocks (connection block keys, connected subagent block): https://developer.salesforce.com/docs/ai/agentforce/guide/ascript-blocks.html
- Agentforce Developer Guide, Multi-Surface Example: Build and Deploy an Enhanced Chat Agent (fallback queue for Messaging Session; escalation flow and message; agent active before routing): https://developer.salesforce.com/docs/ai/agentforce/guide/headless-examples-enhanced-chat-agent.html
- Agentforce Developer Guide, Use Metadata to Move an Agent to a New Org (do not edit retrieved agent metadata): https://developer.salesforce.com/docs/ai/agentforce/guide/agent-dx-deploy-metadata.html
- Apex Developer Guide, Summer '26 (API 67.0), InvocableMethod Annotation (result per input, error wrapping): https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_apex_developer_guide.pdf
- Object Reference, Summer '26, Case (ContactId, Origin, Subject, Description, CaseNumber): https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/object_reference.pdf
- Agentforce Developer Guide, Agent Script Reference: Tools (Reasoning Actions) and Supported Operators (`available when` conditions, comparison operators): https://developer.salesforce.com/docs/ai/agentforce/guide/ascript-ref-tools.html and https://developer.salesforce.com/docs/ai/agentforce/guide/ascript-ref-operators.html

### Carried forward from earlier versions (not re-read on 2026-10-03)

These were not re-read for this revision. help.salesforce.com articles do not return their text to a fetch, so claims that rest only on a Help article are marked UNVERIFIED in the skill.

- Agentforce Service AI — https://help.salesforce.com/s/articleView?id=sf.agentforce_service_agent.htm
- Omni-Channel — https://help.salesforce.com/s/articleView?id=sf.service_presence_intro.htm
- Salesforce Well-Architected User Experience — https://architect.salesforce.com/docs/architect/well-architected/adaptable/adaptable
