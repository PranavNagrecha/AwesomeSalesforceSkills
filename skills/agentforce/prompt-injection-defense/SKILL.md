---
name: prompt-injection-defense
description: "Red-team an Agentforce agent against prompt-injection and jailbreak attacks; codify test cases and guardrails. NOT for general application-security reviews outside the agent boundary."
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
tags:
  - agentforce
  - security
  - prompt-injection
  - red-team
inputs:
  - "Agent topic + actions list"
  - "threat model (who, what data)"
outputs:
  - "Adversarial test set"
  - "Trust Layer policy updates"
  - "topic instruction hardening"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-17
---

# Prompt Injection Defense

Agentforce uses the Einstein Trust Layer for dynamic grounding, masking, and toxicity filtering — but topic instructions and Invocable action scopes still need explicit hardening. Injection attempts include: instruction override, role-reversal, system-prompt leaks, tool-use coercion, and data exfiltration via crafted record content. This skill builds a reusable adversarial test suite and maps findings to concrete guardrails.

## When to Use

Pre-production review for any Agentforce agent that (a) ingests user-controlled text, (b) has write access via Invocables, or (c) is exposed to external/Experience Cloud users. Required for Service agents, Sales agents with Data Cloud grounding, and any custom channel.

Typical trigger phrases that should route to this skill: `red-team my Agentforce agent`, `can my agent be jailbroken`, `how do I prevent prompt injection`, `agent revealed data from another case`.

## Recommended Workflow

1. Enumerate the attack surface: every Invocable action, every grounded DMO/sObject, and every conversational input channel.
2. Build the adversarial test set covering the five OWASP LLM-01 families: instruction override, context leakage, tool-use coercion, exfil via output, and role impersonation.
3. Run each test through Agentforce Testing Center; capture verbatim responses and tool invocations into a results matrix.
4. For each failed test, apply one of four mitigations: (a) narrow the action scope via `with sharing` + field-level checks, (b) add an explicit topic instruction, (c) raise Trust Layer toxicity/PII thresholds, (d) remove the dangerous capability.
5. Re-run the suite until all tests pass; commit the suite to `tests/agentforce/<agent>_adversarial.md` so regressions are caught on every agent change.

## Key Considerations

- Topic instructions are concatenated into the system prompt — a long instruction list dilutes priority. Keep hard constraints in the first 200 tokens.
- Trust Layer masking happens pre-LLM; it doesn't prevent tool-use coercion if the action runs as a privileged user.
- Always test with the least-privileged channel user, not an admin clone.
- Data Cloud grounding returns raw DMO content; a malicious record can contain injection payloads. Sanitize DMO text fields at ingestion when feasible.

## Worked Examples (see `references/examples.md`)

- *Instruction-override test case* — A Service agent has an Invocable `RefundOrder` with guardrail 'only refund orders where Status=Delivered'.
- *Data exfiltration via crafted Case.Description* — Agent reads Case.Description via Data Cloud grounding to answer customer questions.

## Common Gotchas (see `references/gotchas.md`)

- **Testing only with English** — Injection passes the English suite but succeeds in Spanish/French.
- **Trust Layer toxicity threshold too low** — Jailbreaks phrased politely pass filters; toxic but benign content is blocked.
- **Over-indexing on topic instructions** — 100-line topic instructions dilute priority and slow every turn.

## Top LLM Anti-Patterns (full list in `references/llm-anti-patterns.md`)

- Relying on Trust Layer alone — it handles toxicity/PII, not business-policy bypass via tool coercion.
- Adding ad-hoc instructions after incidents instead of maintaining a test suite.
- Using a privileged user for agent execution — scope creep becomes a data-exposure vector.

## Official Sources Used

- Agentforce Developer Guide — https://developer.salesforce.com/docs/einstein/genai/guide/agentforce.html
- Einstein Trust Layer — https://help.salesforce.com/s/articleView?id=sf.generative_ai_trust_layer.htm
- Invocable Actions (Apex) — https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_classes_invocable_action.htm
- Agentforce Testing Center — https://help.salesforce.com/s/articleView?id=sf.agentforce_testing_center.htm
