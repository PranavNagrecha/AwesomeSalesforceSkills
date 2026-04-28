---
name: agent-security-review
description: "Pre-production security checklist for Agentforce deployments: permission scope, data exposure, authentication, logging. NOT for general Salesforce security review (see security-health-check)."
category: agentforce
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Operational Excellence
triggers:
  - "agent go-live security checklist"
  - "review what data the agent can see"
  - "does the agent leak pii"
  - "quarterly agentforce audit"
tags:
  - agentforce
  - security
  - review
  - checklist
inputs:
  - "Agent configuration export"
  - "persona + channel map"
  - "data classification"
outputs:
  - "Signed-off review doc"
  - "remediation ticket list"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-28
---

# Agent Security Review

Agentforce agents touch user PII, internal data, and external APIs with the permissions of whatever user invokes them. A structured review covers four axes: (1) least-privilege user, (2) data classification of every grounding source, (3) action write-scope, (4) audit trail completeness.

## Recommended Workflow

1. Export the agent: topic instructions, Invocable actions, grounding DMOs/sObjects, channel configs. Checksum and archive.
2. Map the agent's run-as user to a dedicated permission set; verify no profile-level permissions leak through.
3. Classify every grounding source: public, internal, confidential, regulated. Redact/mask confidential+regulated fields at the Trust Layer.
4. Enumerate Invocable write scope: which sObjects/fields can be created/updated/deleted. Apply FLS + CRUD checks in Apex; tighten or split the user.
5. Verify audit trail: every Invocable logs to `Agent_Audit__c`; every conversation is retained per retention policy; Shield Event Monitoring streams cover ApexExecution + ContentTransfer.

## Key Considerations

- Default agent-run-as is the invoking user — this is often over-privileged for admin testers. Use automated user for agent invocation.
- Data Cloud grounding can pull data the invoking user cannot see; verify masking at DMO level.
- Invocables bypass `with sharing` if written as `without sharing` — audit every action class's sharing declaration.
- Audit trail must include prompt + response for forensic replay; conversation storage has retention implications (GDPR).

## Worked Examples (see `references/examples.md`)

- *Write-scope tightening* — Service agent can 'Update any Case field' via a generic UpdateRecord action.
- *Regulated-field masking* — RAG grounding includes Contact.Social_Security_Number__c.

## Common Gotchas (see `references/gotchas.md`)

- **Agent run-as has View All** — Agent sees cross-owner records even when user shouldn't.
- **Conversation retention unset** — GDPR subject request cannot locate conversation logs.
- **Shield Event Monitoring not streamed** — Agent anomaly is invisible to SOC.

## Top LLM Anti-Patterns (full list in `references/llm-anti-patterns.md`)

- Running the agent as the invoking user by default — privileged reviewers leak permissions upward.
- Generic 'UpdateRecord' actions — any field becomes attack surface.
- Skipping DMO classification — grounding becomes a data-leak vector.

## Official Sources Used

- Agentforce Developer Guide — https://developer.salesforce.com/docs/einstein/genai/guide/agentforce.html
- Einstein Trust Layer — https://help.salesforce.com/s/articleView?id=sf.generative_ai_trust_layer.htm
- Invocable Actions (Apex) — https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_classes_invocable_action.htm
- Agentforce Testing Center — https://help.salesforce.com/s/articleView?id=sf.agentforce_testing_center.htm
