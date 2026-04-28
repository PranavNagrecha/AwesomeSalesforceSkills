---
name: agentforce-pii-redaction
description: "Redact PII before it reaches Agentforce prompts, models, and logs. Trigger keywords: agentforce pii, pii redaction, data masking llm, einstein trust layer, prompt pii filter, audit pii leakage. Does NOT cover: Shield Platform Encryption at-rest (separate skill), GDPR data subject requests, or classic field-level security policy."
category: agentforce
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Operational Excellence
  - Reliability
triggers:
  - "redact pii before llm"
  - "einstein trust layer pii"
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
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-28
---

# Agentforce PII Redaction

## The Trust Layer

Einstein Trust Layer provides the platform boundary: zero retention,
masking on egress, audit trail. It is not a licence to send raw PII.
Redact **before** the trust layer where you can.

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

Pattern: all three are valid; choose per topic sensitivity.

## Output-Side Redaction

Agent outputs might echo input or retrieved content. Second-pass
redaction on responses before sending back. Trust Layer handles the
baseline; the application can tighten.

## Audit Wiring

- Log the redaction event (field name, strategy) without the value.
- Alert on any PII category that should have been redacted but wasn't.
- Review the audit weekly.

## Recommended Workflow

1. Inventory every field read into prompt context.
2. Classify (Public / Internal / Confidential / Regulated).
3. Choose redaction strategy per field.
4. Centralise redaction in a single Apex/Flow boundary class.
5. Add input-side detection for common PII patterns.
6. Emit audit events on redaction and on any leak.
7. Include PII adversarial cases in the eval suite (see
   `agentforce/agentforce-testing-strategy`).

## Official Sources Used

- Einstein Trust Layer —
  https://help.salesforce.com/s/articleView?id=sf.einstein_trust_layer.htm
- Data Masking For Generative AI —
  https://help.salesforce.com/s/articleView?id=sf.einstein_generative_ai_masking.htm
- Agentforce Audit —
  https://help.salesforce.com/s/articleView?id=sf.einstein_agent_audit.htm
