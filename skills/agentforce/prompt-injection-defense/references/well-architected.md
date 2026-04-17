# Well-Architected Notes — Prompt Injection Defense

**Security:** Prompt injection is the LLM equivalent of SQL injection — the mitigation is separating data from instructions at every boundary (channel, grounding, tool-use).

**Reliability:** A well-tested adversarial suite converts subjective 'agent feels secure' reviews into a pass/fail regression gate.

## Official Sources Used

- Agentforce Developer Guide — https://developer.salesforce.com/docs/einstein/genai/guide/agentforce.html
- Einstein Trust Layer — https://help.salesforce.com/s/articleView?id=sf.generative_ai_trust_layer.htm
- Invocable Actions (Apex) — https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_classes_invocable_action.htm
- Agentforce Testing Center — https://help.salesforce.com/s/articleView?id=sf.agentforce_testing_center.htm
