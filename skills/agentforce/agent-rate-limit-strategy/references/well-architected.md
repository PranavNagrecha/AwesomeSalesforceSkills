# Well-Architected Notes — Agent Rate Limit Strategy

**Scalability:** Per-user budget prevents noisy-neighbor degradation.

**Cost Optimization:** Token consumption is metered; budget limits are tunable per persona; bad-actor loops are capped without hurting the median user.

## Official Sources Used

- Agentforce Developer Guide — https://developer.salesforce.com/docs/einstein/genai/guide/agentforce.html
- Einstein Trust Layer — https://help.salesforce.com/s/articleView?id=sf.generative_ai_trust_layer.htm
- Invocable Actions (Apex) — https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_classes_invocable_action.htm
- Agentforce Testing Center — https://help.salesforce.com/s/articleView?id=sf.agentforce_testing_center.htm
