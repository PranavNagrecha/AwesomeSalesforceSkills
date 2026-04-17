# Well-Architected Notes — Agent Action Error Handling

**Reliability:** Typed responses let the agent and downstream observability react deterministically. Retry-able vs. terminal classification prevents the agent from burning LLM tokens on unrecoverable errors.

**Security:** Raw exception messages can leak record IDs, field names, and SOQL. The typed user_message is sanitized once, at the boundary.

## Official Sources Used

- Agentforce Developer Guide — https://developer.salesforce.com/docs/einstein/genai/guide/agentforce.html
- Einstein Trust Layer — https://help.salesforce.com/s/articleView?id=sf.generative_ai_trust_layer.htm
- Invocable Actions (Apex) — https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_classes_invocable_action.htm
- Agentforce Testing Center — https://help.salesforce.com/s/articleView?id=sf.agentforce_testing_center.htm
