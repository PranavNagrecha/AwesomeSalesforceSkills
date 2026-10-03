---
name: prompt-injection-defense
description: "Red-team an Agentforce agent against prompt-injection and jailbreak attacks; codify adversarial test cases and guardrails, scoped to the agent boundary rather than general application-security review. NOT for the overall agent test plan (topic coverage, golden sets, regression harness) — use agentforce/agentforce-testing-strategy. NOT for keeping PII out of prompts, model calls and logs — use agentforce/agentforce-pii-redaction."
category: agentforce
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Reliability
triggers:
  - "red-team my Agentforce agent"
  - "can my agent be jailbroken"
  - "how do I prevent prompt injection"
  - "agent revealed data from another case"
  - "write adversarial test cases for an Agentforce agent in Testing Center"
  - "harden agent actions so a jailbreak cannot trigger a refund"
tags:
  - agentforce
  - security
  - prompt-injection
  - red-team
inputs:
  - "Agent topic + actions list"
  - "threat model (who, what data)"
  - "Agent API name and the run-as and channel users to test as"
outputs:
  - "Adversarial test set"
  - "Trust Layer policy updates"
  - "topic instruction hardening"
  - "AiEvaluationDefinition file holding the adversarial suite"
dependencies: []
version: 1.1.2
author: Pranav Nagrecha
updated: 2026-10-03
---

# Prompt Injection Defense

Agentforce runs on the Einstein Trust Layer, which adds secure data retrieval, system policies ("Prompt Defense protects the data from prompt injection attacks or jailbreaking"), toxicity scoring, and audit. Subagent instructions and action scopes still need explicit hardening, because data masking is disabled for agents and instructions are interpreted by an LLM. Injection attempts include: instruction override, role-reversal, system-prompt leaks, tool-use coercion, and data exfiltration via crafted record content. This skill builds a reusable adversarial test suite and maps findings to concrete guardrails.

> **Terminology.** Agentforce *topics* were renamed **subagents** in April 2026.
> This skill leads with *subagent*. The older term still appears in metadata and
> API names (GenAiPlugin, `topic_sequence_match`), in older Help articles, and in many orgs; nothing about behaviour
> changed with the rename.

## Adoption Signals

Pre-production review for any Agentforce agent that (a) ingests user-controlled text, (b) has write access via Invocables, or (c) is exposed to external/Experience Cloud users. Required for Service agents, Sales agents with Data Cloud grounding, and any custom channel.

- Required when stakeholders ask whether the agent can be jailbroken — produce a documented adversarial-test pass before exposure.
- Required for any agent that exposes Invocable actions with side effects (DML, callouts, record sharing).

## Questions to Ask Before Configuring

Each question traces to a gotcha in `references/gotchas.md`.

| Question | Why it matters | What a good answer adds | What proper configuration adds over just doing it |
|---|---|---|---|
| "Which actions change data, send messages, or call out, and what does each one check itself?" | Instructions are nondeterministic; the guide says to build sensitive rules into the action (Gotcha 1) | A per-action list of server-side checks | A jailbreak that wins the conversation still loses at the action |
| "Which user does each custom action run as, and does any use without sharing or system mode?" | A custom action adheres to the permissions and sharing of the Apex class or flow it references (Gotcha 2) | Run-as identity and access mode per action | The injection blast radius equals what the user could do anyway |
| "Which grounded fields can an outsider write?" | Web-to-case text, comments, and chat transcripts reach the prompt as context, and masking does not apply to agents (Gotchas 3, 4) | A list of attacker-writable grounding fields | High-risk fields are projected narrowly or excluded |
| "Which languages and channels will the agent face?" | English-only suites miss payloads in other languages, and Trust Layer language support varies (Gotcha 5) | Locales and channels to include in the suite | The suite tests the deployed audience, not a demo |
| "Who runs the suite, and when?" | Agent behaviour is not deterministic, so a suite that is not re-run decays (Gotcha 6) | An AiEvaluationDefinition in source control and a re-run trigger | Every topic or action change gets a pass or fail |
| "How many instructions does each subagent carry today?" | Contradicting or excessive instructions degrade performance, and visual order is not priority (Gotcha 7) | A trimmed instruction set with named verification actions | Fewer, stronger rules that hold under test |

## Recommended Workflow

1. Enumerate the attack surface: every Invocable action and flow action with its run-as identity and access mode, every grounded DMO or sObject field, and every conversational input channel.
2. Build the adversarial test set covering the five OWASP LLM-01 families: instruction override, context leakage, tool-use coercion, exfil via output, and role impersonation, with at least two non-English renderings; store it as an AiEvaluationDefinition (`references/metadata-examples.md`).
3. Run each test through Agentforce Testing Center as the run-as user and each channel user; capture verbatim responses and the topic and action sequence into a results matrix.
4. For each failed test, apply one of four mitigations: (a) move the rule into the action and re-query under user mode, (b) add or sharpen one subagent instruction that names a verification action, (c) narrow the grounding projection, (d) remove the dangerous capability.
5. Run `python3 scripts/check_prompt_injection_defense.py --manifest-dir <project>` to flag system-mode or without-sharing actions, model-asserted Boolean flags, rule-like instructions, and suite coverage gaps.
6. Re-run the suite until all tests pass; commit it beside the agent metadata so regressions are caught on every agent change.

## Key Considerations

- Subagent instructions are interpreted by the LLM. The guide warns that "the LLM doesn't use the visual order of instructions in the Topic Configuration tab to make decisions," so state conditions and sequences explicitly instead of relying on position. UNVERIFIED (2026-10-03): the earlier advice to keep hard constraints in the first 200 tokens was not found in a fetched source.
- Trust Layer data masking is disabled for agents, and masking never decides whether an action may run. It doesn't prevent tool-use coercion if the action runs with broader access than the user.
- Always test with the least-privileged channel user, not an admin clone.
- Data Cloud grounding returns raw DMO content; a malicious record can contain injection payloads. Sanitize DMO text fields at ingestion when feasible.
- The `enableAITrustPromptInjectionDetection` field on EinsteinAISettings is "Reserved for internal use"; there is no documented customer setting to tune injection detection.

## Worked Examples (see `references/examples.md` and `references/metadata-examples.md`)

- *Instruction-override test case* — A Service agent has an Invocable `RefundOrder` with guardrail 'only refund orders where Status=Delivered'.
- *Data exfiltration via crafted Case.Description* — Agent reads Case.Description via Data Cloud grounding to answer customer questions.
- *Adversarial suite as metadata*: an AiEvaluationDefinition with override, leakage, coercion, and non-English cases, plus a hardened GenAiPlugin topic.

## Common Gotchas (see `references/gotchas.md`)

- **Testing only with English** — Injection passes the English suite but succeeds in Spanish/French.
- **Treating instructions as enforcement**: The guide says to build sensitive or deterministic business rules into the action itself.
- **Over-indexing on subagent instructions** — 100-line subagent instructions dilute priority and slow every turn.

## Top LLM Anti-Patterns (full list in `references/llm-anti-patterns.md`)

- Relying on Trust Layer alone: it handles toxicity, system policies, and (outside agents) masking, not business-policy bypass via tool coercion.
- Adding ad-hoc instructions after incidents instead of maintaining a test suite.
- Using a privileged user for agent execution — scope creep becomes a data-exposure vector.

## Official Sources Used

- Quickstart Your Einstein Generative AI Solution (Spring '26): https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/generative_ai.pdf
- Metadata API Developer Guide, v67.0 (AiEvaluationDefinition, GenAiPlugin, EinsteinAISettings): https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf
- Apex Developer Guide, v67.0 (sharing and user mode): https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_apex_developer_guide.pdf
- Agentforce Developer Guide — https://developer.salesforce.com/docs/einstein/genai/guide/agentforce.html
- Einstein Trust Layer — https://help.salesforce.com/s/articleView?id=sf.generative_ai_trust_layer.htm
- Invocable Actions (Apex) — https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_classes_invocable_action.htm
- Agentforce Testing Center — https://help.salesforce.com/s/articleView?id=sf.agentforce_testing_center.htm
