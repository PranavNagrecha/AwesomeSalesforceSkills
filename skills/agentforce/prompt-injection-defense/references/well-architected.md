# Well-Architected Notes — Prompt Injection Defense

**Security:** prompt injection is an authorization problem wearing a language-model
costume. The durable mitigation is that no action trusts a value the model produced:
every action re-establishes its own facts under the running user's access, and topic
instructions are treated as a way to reduce attempt frequency rather than as a control.

**Reliability:** a committed adversarial suite, run under the agent's real run-as
identity, converts "the agent feels safe" into a pass/fail gate that survives the next
topic edit. Without it, guardrails decay silently because agent behaviour is not
deterministic.

## Official Sources Used

- Enforcing Object and Field Permissions in Apex (WITH USER_MODE, stripInaccessible) — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_classes_perms_enforcing.htm
- Einstein Trust Layer — masking and toxicity filtering boundaries — https://help.salesforce.com/s/articleView?id=sf.generative_ai_trust_layer.htm
- Agentforce Testing Center — running a committed adversarial suite — https://help.salesforce.com/s/articleView?id=sf.agentforce_testing_center.htm
- Agentforce Developer Guide — topics, actions and grounding — https://developer.salesforce.com/docs/einstein/genai/guide/agentforce.html
- InvocableMethod annotation — the Request/Response contract an action must honour — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_classes_annotation_InvocableMethod.htm

Threat taxonomy referenced by name only: OWASP Top 10 for LLM Applications, LLM01
(Prompt Injection). It is not a Salesforce source and is not authoritative for platform
behaviour.
