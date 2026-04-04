---
name: einstein-trust-layer
description: "Use this skill when configuring, auditing, or troubleshooting Salesforce Einstein Trust Layer security controls for generative AI features including Agentforce, Einstein Copilot, and Prompt Builder. Trigger keywords: trust layer, data masking, zero data retention, ZDR, toxicity detection, AI audit trail, grounding controls, PII masking LLM, Einstein generative AI security. NOT for agent action development, LWC component authoring, or non-AI data governance (see data-quality-and-governance skill for that)."
category: agentforce
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Reliability
triggers:
  - "how do I prevent PII from being sent to the LLM in Salesforce"
  - "does Salesforce store my data with OpenAI or external AI providers"
  - "how do I enable the Einstein Trust Layer audit trail for compliance"
  - "toxicity detection is blocking responses that should be allowed"
  - "data masking is not working for agent prompts in my org"
  - "how do I configure zero data retention for Einstein AI features"
tags:
  - einstein-trust-layer
  - data-masking
  - zero-data-retention
  - toxicity-detection
  - audit-trail
  - generative-ai-security
inputs:
  - Salesforce org with Einstein Generative AI enabled
  - Data 360 provisioned (required for Trust Layer functionality)
  - Target Einstein features in scope (Agentforce, Copilot, Prompt Builder, embedded features)
  - Compliance or data-residency requirements (e.g., EU data residency, PCI, HIPAA)
outputs:
  - Configured Trust Layer security controls (data masking, toxicity detection, ZDR verification)
  - Enabled and accessible audit trail for AI interaction logging
  - Decision guidance on grounding strategy and data exposure scope
  - Review checklist confirming security posture for generative AI deployments
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-04
---

# Einstein Trust Layer

This skill activates when a practitioner needs to configure, validate, or troubleshoot the Einstein Trust Layer — the security infrastructure Salesforce places between users, CRM data, and external LLMs. It covers all five protective components: secure data retrieval and grounding, data masking, zero data retention, toxicity detection, and audit trail.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Data 360 must be provisioned.** The Einstein Trust Layer depends on Data 360 for audit trail storage. Without it, audit trail cannot be enabled and some Trust Layer features will be unavailable.
- **Einstein Generative AI must be turned on.** Navigate to Setup > Einstein Setup and toggle "Turn on Einstein" to On before accessing the Trust Layer configuration page.
- **Which Einstein features are in scope?** Data masking behavior and applicability differ by feature. As of Spring '25, data masking is available for embedded features (Service Replies, Work Summaries, Prompt Builder previews) but disabled for Agentforce agents by default. Confirm the features before setting expectations.
- **The most common wrong assumption:** Practitioners assume Trust Layer controls are on by default and apply uniformly. In practice, data masking must be explicitly enabled, and it does not apply to all Einstein features identically.
- **Context window constraint:** When data masking is active, all models are limited to a context size of 65,536 tokens. Prompts that exceed this limit will fail or be truncated.

---

## Core Concepts

### Zero Data Retention (ZDR)

Salesforce holds contractual zero data retention agreements with external LLM providers (including OpenAI). Under these agreements, prompts and responses sent through the LLM gateway are never stored or used for model training by the provider. Data passes through OpenAI's enterprise API and is discarded immediately after the response is generated — it does not persist outside Salesforce infrastructure.

ZDR applies specifically to data sent to external LLMs. It does not mean that Salesforce itself does not store anything — the audit trail within Data 360 retains interaction records for compliance purposes.

### Data Masking

Before a prompt is sent to an external LLM, the Trust Layer uses named entity recognition (NER) and pattern-matching to identify PII and PCI data. Detected entities are replaced with typed placeholders (e.g., `PERSON_0`, `EMAIL_0`, `CREDITCARD_0`). A temporary mapping is held within the Trust Layer. When the LLM returns its response, the Trust Layer demasks — restoring original values before presenting the result to the user.

Default masked data types include: names (individual and organizational), email addresses, phone numbers (business and mobile), credit card numbers, and US Social Security Numbers. Administrators can configure which data types to mask from the setup UI.

Important constraints:
- No model can guarantee 100% detection accuracy. Cross-region or multi-country data patterns may reduce detection effectiveness.
- Data masking requires valid-format data to trigger. A malformed SSN or an invalid credit card number will not be masked.
- Context window is capped at 65,536 tokens when data masking is active.
- There is no programmatic way to handle masked data from the Models API — masking is fully managed by the Trust Layer.
- Policy updates can take a few minutes to propagate after saving.

### Toxicity Detection

After the LLM returns a response, the Trust Layer scores it for harmful content using a combination of rule-based filtering and a Salesforce Research transformer model (Flan-T5-base, trained on approximately 2.3 million prompts). Toxicity is scored across multiple categories including toxicity (general rudeness/unreasonableness), hate speech, violence, physical harm, sexual content, and profanity. The overall score is a composite value ranging from 0 to 1, with 1 representing maximum toxicity.

The toxicity score accompanies the response and is recorded in the audit trail. Applications can consume the score to decide whether to present the response to the user.

### Grounding Controls

Grounding connects AI prompts to organizational data so responses are contextually accurate. The Trust Layer supports three grounding modes:

- **Client-side grounding:** Merge fields on a record page populate with the currently displayed record's data during user interactions.
- **Server-side grounding:** Flows or Apex calls query the database directly to inject context at processing time.
- **Dynamic grounding:** Data providers (Flows, Data Cloud) are called at prompt execution time to retrieve related information, enabling semantic retrieval and external API integration.

Grounding determines what CRM data is exposed to the LLM. Prompt defense is applied post-grounding to add guardrail instructions that reduce prompt injection risk and hallucination.

### Audit Trail

The audit trail records every AI interaction passing through the Trust Layer. Each record includes: the original prompt, safety scores from toxicity detection, the raw LLM output, user acceptance/rejection decision, and any user modifications before the output was used. Records are stored in Data 360.

Audit trail is not active out of the box — it requires explicit enablement. Retention period is configurable. The audit trail is accessible for compliance review and can be surfaced through reports and dashboards within the org.

---

## Common Patterns

### Pattern: Enabling Trust Layer Security Controls for a New Org

**When to use:** When activating Einstein Generative AI for the first time and establishing the security baseline before deploying any AI feature to users.

**How it works:**
1. Verify Data 360 is provisioned (required dependency).
2. Navigate to Setup > Einstein Setup. Toggle "Turn on Einstein" to On.
3. Click "Go to Einstein Trust Layer."
4. Enable "Large Language Model Data Masking." Select which sensitive data categories to mask (names, emails, phones, SSNs, credit cards are recommended as a default).
5. Enable the audit trail. Configure the retention period to match your compliance policy.
6. Verify that the Zero Data Retention agreement with external providers is active (confirm in the Trust Layer setup UI).
7. Test data masking by previewing a prompt template in Prompt Builder with a record containing known PII — confirm placeholders appear in the preview and are restored in the response.

**Why not skip setup:** Without explicit enablement of data masking, PII fields in grounded prompts are sent in plain text to the external LLM. ZDR alone does not prevent exposure during processing — masking prevents the LLM from ever seeing raw PII.

### Pattern: Diagnosing Toxicity Detection False Positives

**When to use:** When valid AI responses are being suppressed or flagged incorrectly, causing user-facing errors or missing outputs.

**How it works:**
1. Access the audit trail in Data 360 and find the interaction records for the flagged responses.
2. Review the toxicity scores by category. A composite score near 1 on a specific subcategory (e.g., violence) in a legitimate service context indicates a false positive from context misinterpretation.
3. Review the original prompt and grounding data — prompt injection or ambiguous field values can raise scores artificially.
4. Adjust the prompt template to provide clearer context instructions to the LLM (via prompt defense additions).
5. Re-test with the updated template and monitor audit trail scores.

**Why not disable toxicity detection:** Toxicity detection is a Trust Layer control that cannot be selectively disabled per-feature without removing it org-wide. The correct remediation is prompt and grounding refinement.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| PII in CRM must not reach external LLM | Enable data masking with all PII/PCI categories selected | Masking intercepts before transmission; ZDR alone does not prevent in-flight exposure |
| Compliance requires logs of all AI interactions | Enable audit trail with retention period matching policy; store in Data 360 | Audit trail is the only mechanism for interaction-level logging in the Trust Layer |
| Prompt responses seem unaware of record context | Use client-side grounding for record-page features; dynamic grounding for server-side flows | Grounding mode must match the execution context or record data will be missing |
| EU data residency requirement | Confirm org is provisioned in an EU data center; Trust Layer routes through Salesforce infrastructure, not directly to LLM providers | LLM gateway keeps data within Salesforce routing; EU org provisioning determines residency |
| Agents not masking PII in prompts | Verify the feature scope — data masking for agents may be disabled; check release notes for current coverage | As of Spring '25, data masking is not applied to Agentforce agents by default |
| Toxicity detection blocking valid responses | Review audit trail scores by category; refine prompt template instructions | Detection uses ML scoring; context-specific guardrail instructions reduce false positives |

---


## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner activating this skill:

1. Gather context — confirm the org edition, relevant objects, and current configuration state
2. Review official sources — check the references in this skill's well-architected.md before making changes
3. Implement or advise — apply the patterns from Core Concepts and Common Patterns sections above
4. Validate — run the skill's checker script and verify against the Review Checklist below
5. Document — record any deviations from standard patterns and update the template if needed

---

## Review Checklist

Run through these before marking Trust Layer configuration complete:

- [ ] Data 360 is provisioned and accessible in the org
- [ ] Einstein Generative AI is enabled in Einstein Setup
- [ ] Data masking is enabled with the correct sensitive data categories selected
- [ ] Audit trail is enabled with a retention period aligned to compliance requirements
- [ ] Zero Data Retention agreement with external LLM providers is confirmed active
- [ ] Prompt templates tested in Prompt Builder confirm PII placeholders appear (not raw values) in preview
- [ ] Toxicity detection is active and audit trail records show toxicity scores
- [ ] Grounding mode (client-side, server-side, dynamic) matches the feature's execution context
- [ ] EU data residency requirements confirmed against org data center provisioning

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Data masking is disabled for Agentforce agents by default** — Practitioners who enable data masking in Trust Layer setup assume it applies to all AI features. As of Spring '25, data masking applies to embedded features (Service Replies, Work Summaries, Prompt Builder previews) but is not applied to agent prompts. PII in agent-grounded prompts can be sent in plain text to the external LLM. Always check release notes and the feature-specific Trust Layer coverage before assuming masking is active.

2. **Zero data retention applies to external LLMs only, not to the audit trail** — ZDR means the external LLM provider (e.g., OpenAI) does not retain the data after processing. The audit trail within Salesforce Data 360 does store interaction records, including the original prompt and LLM output. Practitioners who cite ZDR as a reason not to configure audit trail retention policies are creating a compliance gap — the audit trail must be independently governed.

3. **Invalid-format PII is not masked** — The masking engine validates data format before applying placeholders. A social security number with incorrect formatting, a malformed email, or an invalid credit card number will pass through to the LLM unmasked. This is a silent failure — there is no error or warning. Testing masking with realistic production-format data is required to validate coverage.

4. **Context window shrinks to 65,536 tokens when data masking is active** — Large prompt templates or heavily grounded prompts that work without masking may exceed the reduced context window and fail at runtime. Prompt size must be validated with masking active, not just in isolation.

5. **Audit trail requires explicit activation and is not retroactive** — Interactions that occur before audit trail is enabled are not logged. There is no backfill mechanism. Organizations that enable generative AI features before setting up the audit trail will have a compliance gap for that period.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Trust Layer configuration checklist | Completed checklist confirming masking, ZDR, toxicity, and audit trail status |
| Audit trail review | Interaction records in Data 360 showing prompt, toxicity scores, LLM output, and user decision |
| Prompt Builder test results | Masked preview output confirming PII substitution is working before feature goes live |
| Data masking policy | Configured sensitive data category selections in Trust Layer setup |

---

## Related Skills

- agentforce/agentforce-agent-design — use alongside this skill when building agents to validate what data is grounded and whether Trust Layer coverage applies to agent prompts
- data/data-quality-and-governance — for broader data governance, classification, and Shield Platform Encryption concerns outside of AI interaction security
