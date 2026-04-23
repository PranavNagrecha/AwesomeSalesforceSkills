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

- Agentforce Service AI — https://help.salesforce.com/s/articleView?id=sf.agentforce_service_agent.htm
- Omni-Channel — https://help.salesforce.com/s/articleView?id=sf.service_presence_intro.htm
- Salesforce Well-Architected User Experience — https://architect.salesforce.com/docs/architect/well-architected/adaptable/adaptable
