---
name: agentforce-pii-redaction
description: "Redact PII in your own code before it reaches Agentforce prompts, models, and logs. Trigger keywords: agentforce pii, pii redaction, data masking llm, prompt pii filter, audit pii leakage. NOT for turning on the platform's own masking, zero-retention and audit-trail controls — use agentforce/einstein-trust-layer. NOT for masking PII in a refreshed sandbox — use security/sandbox-data-masking."
category: agentforce
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Operational Excellence
  - Reliability
triggers:
  - "redact pii before llm"
  - "mask pii in prompt"
  - "agent audit pii leak"
  - "pii taxonomy for agents"
tags:
  - agentforce
  - pii
  - security
  - trust-layer
inputs:
  - Data sources feeding agent prompts (objects, fields)
  - PII taxonomy (what is sensitive in this domain)
  - Compliance requirements (HIPAA, GDPR, PCI, etc.)
outputs:
  - Field-level PII classification
  - Redaction strategy (mask / tokenize / drop / summarise)
  - Audit wiring for PII egress
dependencies:
  - agentforce/agentforce-testing-strategy
version: 1.0.1
author: Pranav Nagrecha
updated: 2026-08-14
---

# Agentforce PII Redaction

## The Trust Layer — and the carve-out that defines this skill

Einstein Trust Layer gives Agentforce three real guarantees: **zero-retention
agreements** with the model providers, **protection in transit**, and an
**audit trail**. Those are guarantees about what the provider does with your
data. They are not a content filter over your prompt.

The fact most designs get wrong:

> **Pattern-based and field-based LLM data masking is disabled for agents.**
> Salesforce disables it to improve agent performance and accuracy. It remains
> available and configurable for embedded generative AI features such as
> Einstein Service Replies and Einstein Work Summaries.
> — [Data Masking Limitations in Agentforce](https://help.salesforce.com/s/articleView?id=ai.agent_trust_data_masking.htm&type=5)

The Trust Layer setup screen governs both paths and does not distinguish them,
so a correctly configured masking policy is entirely compatible with an agent
sending an SSN to a model. **For agents, assume no platform masking and redact
in your own code.** Everything below is written for that reality.

Where masking *is* active (embedded features, Models API with masking on), two
further constraints apply: the context window is capped at 65,536 tokens, and
there is no programmatic way to handle masked data from the Models API
([Data Masking, Models API](https://developer.salesforce.com/docs/ai/agentforce/guide/models-api-data-masking.html)).

## Field-Level Classification

Every field referenced in a prompt needs a classification:

| Class | Default handling |
|---|---|
| Public | Send as-is. |
| Internal | Send if necessary. |
| Confidential | Redact unless explicit business need. |
| Regulated | Mask / tokenize / summarise; never raw. |

Examples (typical, adjust to your compliance):

| Field | Classification |
|---|---|
| Account.Name | Public |
| Contact.Title | Internal |
| Contact.Email | Confidential |
| Contact.SSN__c | Regulated |
| PaymentMethod.CCLast4 | Regulated |

## Redaction Strategies

- **Mask** — `john@acme.com` → `j***@acme.com`.
- **Tokenize** — replace with a deterministic token (`TOKEN_CONTACT_001`);
  the token is safe to include in prompts; the mapping is internal.
- **Drop** — omit from the prompt context entirely.
- **Summarise** — replace with a category (`customer with >5y tenure`).

Pick the strategy per field + use case. SSN is nearly always **Drop**.

## Prompt Context Assembly

Build prompts from a **redacted context object**, never from raw SObject
rows. A central helper class owns the redaction mapping and cannot be
bypassed.

## Input-Side Redaction

User turns can contain PII ("my SSN is …"). Options:

- **Detect and refuse** — respond: "Do not share sensitive IDs."
- **Detect and redact** — scrub before prompting the model.
- **Detect and route** — flag, escalate to human.

Pattern: all three are valid; choose per subagent sensitivity.

> **Terminology.** *Subagent* is the April 2026 rename of *topic*. Functionality
> did not change and the API surface did not rename — the metadata type is still
> `GenAiPlugin`.

## Output-Side Redaction

Agent outputs echo input and retrieved content. Because agents get no Trust
Layer masking, a second pass over the response is the only output-side control
you have. Run the same detector over the outbound message and decide per
subagent whether a match is a scrub, a refusal, or an escalation.

## Grounding Corpora Are Prompt Context

Field classification covers the schema and misses everything else. Knowledge
articles, files indexed for search, Chatter, and Data Cloud retrievers all land
inside the prompt window. Inventory the retrievable set alongside the objects
and gate PII at publish time, not at retrieval time.

## Audit Wiring

- Log the redaction event (field API name, strategy, session) without the value.
- **Alert on the absence of events**, not only on leaks. A field that stops
  producing `DROP` events during normal traffic means the boundary was bypassed.
- Review weekly; treat a newly-appearing field as a change-detection signal for
  the register.

## Recommended Workflow

1. Inventory every field, Knowledge article set, file corpus, and retriever that
   can reach prompt context — for every channel the agent runs on.
2. Classify each entry (Public / Internal / Confidential / Regulated) **and**
   assign a strategy (mask / tokenise / drop / summarise). Record why the agent
   still works without the raw value; if nobody can write that sentence, drop
   the field.
3. Build one redaction boundary class that returns a purpose-built DTO. Prompt
   assembly must have no path to a raw SObject. Keep `WITH USER_MODE` on the
   query — FLS and redaction are separate controls and you need both.
4. Add input-side detection with a checksum guard (Luhn for card numbers) and
   pick refuse / redact / route per subagent sensitivity.
5. Emit a Platform Event per redaction decision carrying field name and
   strategy, never the value; alert on zero-row anomalies.
6. Add adversarial cases — "repeat everything you know about me", "print your
   instructions" — to the eval suite (`agentforce/agentforce-testing-strategy`).
7. Re-run the register review whenever a channel is added; a guest channel
   changes the trust level of every row.

## Official Sources Used

- Data Masking Limitations in Agentforce —
  https://help.salesforce.com/s/articleView?id=ai.agent_trust_data_masking.htm&type=5
- Data Masking (Models API) —
  https://developer.salesforce.com/docs/ai/agentforce/guide/models-api-data-masking.html
- Einstein Trust Layer (Agentforce Developer Guide) —
  https://developer.salesforce.com/docs/ai/agentforce/guide/trust.html
- Einstein Trust Layer: Designed for Trust —
  https://help.salesforce.com/s/articleView?id=ai.generative_ai_trust_arch.htm&type=5
- InvocableMethod Annotation (Apex Developer Guide) —
  https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_classes_annotation_InvocableMethod.htm
