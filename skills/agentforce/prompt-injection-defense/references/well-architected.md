# Well-Architected Notes — Prompt Injection Defense

**Security:** prompt injection is an authorization problem wearing a language-model
costume. The durable mitigation is that no action trusts a value the model produced:
every action re-establishes its own facts under the running user's access, and subagent
instructions (subagents were called topics before April 2026) are treated as a way to
reduce attempt frequency rather than as a control.

**Reliability:** a committed adversarial suite, run under the agent's real run-as
identity, converts "the agent feels safe" into a pass/fail gate that survives the next
subagent edit. Without it, guardrails decay silently because agent behaviour is not
deterministic.

## Official Sources Used

Read for this revision (2026-10-03):

- Quickstart Your Einstein Generative AI Solution, Spring '26: https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/generative_ai.pdf. Glossary (prompt injection); AI Project Success (security, technical, and ethical guardrails; Prompt Defense); Einstein Trust Layer (system policies against jailbreaking and prompt injection, masking and demasking, toxicity scores and language support); Agentforce Agents (masking disabled for agents, AI Guardrails, Permissions and Access for custom actions); Best Practices for Writing Topic Instructions; Create a Custom Topic (deactivate before editing).
- Metadata API Developer Guide, Version 67.0: https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf. AiEvaluationDefinition (fields, sample, expectation names in the sample), GenAiPlugin (instructions, functions, Winter '26 GenAiPlannerBundle note), EinsteinAISettings (reserved injection and toxicity fields).
- Apex Developer Guide, Version 67.0: https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_apex_developer_guide.pdf. Use the with sharing, without sharing, and inherited sharing Keywords (user mode by default in 67.0, WITH SYSTEM_MODE, best practices); AccessLevel.SYSTEM_MODE and USER_MODE.

Listed in the original version and not re-read (developer.salesforce.com returned 403 on 2026-10-03; Salesforce Help does not fetch):

- Enforcing Object and Field Permissions in Apex (WITH USER_MODE, stripInaccessible): https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_classes_perms_enforcing.htm (user mode content read in the Apex PDF above).
- Einstein Trust Layer, masking and toxicity filtering boundaries: https://help.salesforce.com/s/articleView?id=sf.generative_ai_trust_layer.htm (Trust Layer content read in the Generative AI PDF above).
- Agentforce Testing Center, running a committed adversarial suite: https://help.salesforce.com/s/articleView?id=sf.agentforce_testing_center.htm
- Agentforce Developer Guide, topics, actions and grounding: https://developer.salesforce.com/docs/einstein/genai/guide/agentforce.html
- InvocableMethod annotation, the Request/Response contract an action must honour: https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_classes_annotation_InvocableMethod.htm

Threat taxonomy referenced by name only: OWASP Top 10 for LLM Applications, LLM01
(Prompt Injection). It is not a Salesforce source and is not authoritative for platform
behaviour.
