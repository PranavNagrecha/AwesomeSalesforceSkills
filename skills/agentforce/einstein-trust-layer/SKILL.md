---
name: einstein-trust-layer
description: "Configure, audit, or troubleshoot Einstein Trust Layer security controls for generative AI features including Agentforce, Einstein Copilot, and Prompt Builder. Trigger keywords: trust layer, data masking, zero data retention, ZDR, toxicity detection, AI audit trail, grounding controls, PII masking LLM, Einstein generative AI security. NOT for redaction you build yourself in prompt-assembly code — use agentforce/agentforce-pii-redaction. NOT for org-wide AI governance and policy-as-code architecture — use architect/ai-governance-architecture."
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
  - "einstein trust layer isn't working"
  - "we're having issues with einstein trust layer"
  - "verify that data masking hides PII in a prompt template before go-live"
  - "build a Data Cloud report of masked prompts and toxicity scores for an audit"
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
version: 1.0.2
author: Pranav Nagrecha
updated: 2026-10-03
---

# Einstein Trust Layer

This skill activates when a practitioner needs to configure, validate, or troubleshoot the Einstein Trust Layer — the security infrastructure Salesforce places between users, CRM data, and external LLMs. It covers all five protective components: secure data retrieval and grounding, data masking, zero data retention, toxicity detection, and audit trail.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Data 360 must be provisioned.** The Einstein Trust Layer depends on Data 360 for audit trail storage. Without it, audit trail cannot be enabled and some Trust Layer features will be unavailable.
- **Einstein Generative AI must be turned on.** Navigate to Setup > Einstein Setup and toggle "Turn on Einstein" to On before accessing the Trust Layer configuration page.
- **Which Einstein features are in scope?** Data masking behavior and applicability differ by feature. The Generative AI guide states: "Data masking through the Einstein Trust Layer is disabled to improve the performance and accuracy of agents." Masking applies to Prompt Builder and features that use prompt templates; "LLM Data Masking isn't always available in all features." Confirm the features before setting expectations.
- **The most common wrong assumption:** Practitioners assume Trust Layer controls apply uniformly. In practice, masking does not apply to agents, field-based masking covers only record merge fields and related lists, and audit data is collected only after data collection is turned on. Correction (2026-10-03): earlier versions said data masking must be explicitly enabled; the Set up Einstein Trust Layer steps say "Data Masking is enabled by default," with the most commonly used data types turned on at initial setup.
- **Context window constraint:** Earlier versions said that when data masking is active, all models are limited to a context size of 65,536 tokens. UNVERIFIED (2026-10-03): this figure does not appear in the Generative AI guide; Prompt Builder instead documents that "When a prompt is too large for the model to use, a summary is generated automatically in the Resolution panel." Test large prompts with masking on.

---

## Core Concepts

### Zero Data Retention (ZDR)

Salesforce holds zero data retention agreements with external LLM providers; the guide names OpenAI and Azure OpenAI. Under the policy, "data sent to the LLM from Salesforce isn't retained and is deleted after a response is sent back to Salesforce," no data is used for model training or product improvements by third-party LLMs, and no human at the provider looks at it. Data passes through OpenAI's enterprise API and is discarded immediately after the response is generated; it does not persist outside Salesforce infrastructure.

ZDR applies specifically to data sent to external LLMs. It does not mean that Salesforce itself does not store anything: audit and feedback data are stored in your Data Cloud instance for as long as you choose, and "additionally, audit and feedback data are stored by Salesforce for 30 days for compliance purposes."

### Data Masking

Before a prompt is sent to an external LLM, the Trust Layer identifies sensitive data two ways. Pattern-based masking uses regular expressions, context words, and machine learning models (for names of people and companies) across all prompt text. Field-based masking uses Shield Platform Encryption or data classification metadata, and "supports only merge fields that are referenced in record merge fields and related lists." Detected values are replaced with placeholder text, and the Trust Layer "temporarily stores the relationship between the original entities and their respective placeholders" to demask the response. UNVERIFIED (2026-10-03): the exact placeholder format (for example `PERSON_0`) is not shown in the guide; Prompt Builder's View Your Data Masking Details dialog shows the real placeholders.

Pattern-based data types are Company Name, Credit Card (16 or 17 digits), Email Address, IBAN, Name, Passport, and Phone Number in English, French, German, Italian, Japanese, and Spanish, plus US driver's license, US ITIN, and US Social Security number in English (United States) only. "At initial setup, the most commonly used entries are turned on, and less frequently used entries are off." Administrators choose types in Einstein Trust Layer setup.

Important constraints:
- No model can guarantee 100% detection accuracy. Cross-region or multi-country data patterns may reduce detection effectiveness.
- Data masking requires valid-format data to trigger. A malformed SSN or an invalid credit card number will not be masked.
- UNVERIFIED (2026-10-03): the 65,536-token context cap with masking active (see Before Starting).
- UNVERIFIED (2026-10-03): that there is no programmatic way to handle masked data from the Models API.
- Changes to masking entities "can take up to a few minutes" to take effect.

### Toxicity Detection

After the LLM returns a response, the Trust Layer scans it for toxicity and records "a toxicity confidence score" and categories in Data Cloud. UNVERIFIED (2026-10-03): the model details from the original version (rule-based filtering plus a Flan-T5-base transformer trained on about 2.3 million prompts) come from a blog post, not the guide. Scores run from 0 to 1. For the safety category, 1 is safest and 0.5 to 1 is considered safe; for every other category, 0.5 and above is considered toxic. "When the isToxicityDetected field is false, it doesn't necessarily mean there isn't toxicity."

The toxicity score accompanies the response and is recorded in the audit trail. Applications can consume the score to decide whether to present the response to the user.

### Grounding Controls

Grounding connects AI prompts to organizational data so responses are contextually accurate. The guide lists merge fields for record fields, flows, Apex, Data Cloud DMOs, and related lists, and states that retrieval is "based on the permissions of the user executing the prompt" and preserves role-based controls and field-level security. The original version described three grounding modes; UNVERIFIED (2026-10-03), as these names come from a blog post:

- **Client-side grounding:** Merge fields on a record page populate with the currently displayed record's data during user interactions.
- **Server-side grounding:** Flows or Apex calls query the database directly to inject context at processing time.
- **Dynamic grounding:** Data providers (Flows, Data Cloud) are called at prompt execution time to retrieve related information, enabling semantic retrieval and external API integration.

Grounding determines what CRM data is exposed to the LLM. Prompt defense is applied post-grounding to add guardrail instructions that reduce prompt injection risk and hallucination.

### Audit Trail

The audit trail records every AI interaction passing through the Trust Layer. Each record includes: the original prompt, safety scores from toxicity detection, the raw LLM output, user acceptance/rejection decision, and any user modifications before the output was used. Records are stored in Data 360.

To see audit data you must turn on Einstein generative AI data collection and storage and install the audit and feedback report package. Data lands in the default data space, Data Cloud refreshes the streams once every hour, and on average each LLM round trip ingests 24 records, which consume Data Cloud credits. Use the GenAIGatewayRequest report (Prompt, MaskedPrompt, promptTokens) to verify masking and the GenAIGatewayResponse with GenAIContentCategory report (DetectorType, Category, Value) to review toxicity.

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


## Questions to Ask Before Configuring

Each question traces to a gotcha in `references/gotchas.md`.

| Question | Why it matters | What a good answer adds | What proper configuration adds over just doing it |
|---|---|---|---|
| "Which features will send customer data to an LLM: agents, prompt templates, or embedded features?" | Masking is disabled for agents and isn't available in all features (Gotcha 1) | A feature list with masking coverage per feature | Nobody tells compliance that agent prompts are masked when they are not |
| "Which sensitive fields arrive through Flow or Apex merge fields rather than record fields?" | Field-based masking covers only record merge fields and related lists (Gotcha 4) | A list of fields that rely on pattern-based masking alone | Sensitive values from code paths are classified, reshaped, or kept out |
| "Which countries and languages do the records come from?" | Pattern types and phone formats are language and region specific, and no model is 100% accurate (Gotcha 3) | The data types and locales to test | Masking is tested on the data the org really holds |
| "Is data collection on, and who reads the audit reports?" | Audit data exists only after collection is turned on, and each round trip ingests about 24 Data Cloud records (Gotchas 5, 6) | An owner, a report, and a credit estimate | Evidence exists on day one and the credit bill is expected |
| "Will this be tested in a sandbox?" | Masking configuration, Data Cloud grounding, and audit data aren't available in sandbox staging environments (Gotcha 7) | A production-like test plan for those three | Go-live is not the first time masking is checked |
| "Must LLM requests stay in a region?" | Geo-aware routing falls back to the US when a model isn't nearby, and that can't be disabled (Gotcha 9) | Model and provider choices per residency rule | Residency claims match how requests are routed |

## Recommended Workflow

1. Confirm prerequisites: Einstein Generative AI on, Data Cloud configured, and the list of features in scope with their masking coverage (the Questions table).
2. Commit the deployable switches (EinsteinAISettings `enableTrustPIIMasking` and `enableAIFeedbackWithDC`, EinsteinGptSettings provider blocks and region fallback) from `references/metadata-examples.md`. In Setup, open Einstein Trust Layer, review the pattern-based data types, and turn on masking for Shield Platform Encryption, compliance categories, and sensitivity levels; tag sensitive fields in Object Manager.
3. Turn on Einstein generative AI data collection and storage, and install the audit and feedback report package.
4. Verify masking in Prompt Builder preview (View Your Data Masking Details) and in the GenAIGatewayRequest report, using records with each data type and locale the org holds.
5. Run `python3 scripts/check_einstein_trust_layer.py --manifest-dir <metadata root>` to catch disabled settings, region fallback, direct LLM callouts, and Flow or Apex merge fields that only pattern-based masking can cover.
6. Review toxicity with the GenAIGatewayResponse with GenAIContentCategory report, and record the masking, audit, and residency decisions for compliance.

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

1. **Data masking is disabled for Agentforce agents**: Practitioners who enable data masking in Trust Layer setup assume it applies to all AI features. The guide states that "Data masking through the Einstein Trust Layer is disabled to improve the performance and accuracy of agents." PII in agent-grounded prompts can be sent in plain text to the external LLM. Always check release notes and the feature-specific Trust Layer coverage before assuming masking is active.

2. **Zero data retention applies to external LLMs only, not to the audit trail** — ZDR means the external LLM provider (e.g., OpenAI) does not retain the data after processing. The audit trail within Salesforce Data 360 does store interaction records, including the original prompt and LLM output. Practitioners who cite ZDR as a reason not to configure audit trail retention policies are creating a compliance gap — the audit trail must be independently governed.

3. **Invalid-format PII is not masked** — The masking engine validates data format before applying placeholders. A social security number with incorrect formatting, a malformed email, or an invalid credit card number will pass through to the LLM unmasked. This is a silent failure — there is no error or warning. Testing masking with realistic production-format data is required to validate coverage.

4. **Context window shrinks to 65,536 tokens when data masking is active** — UNVERIFIED (2026-10-03): not found in the Generative AI guide. Large prompt templates or heavily grounded prompts that work without masking should still be validated with masking active.

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

- agentforce/agentforce-agent-creation: use alongside this skill when building agents to validate what data is grounded and whether Trust Layer coverage applies to agent prompts
- data/data-quality-and-governance — for broader data governance, classification, and Shield Platform Encryption concerns outside of AI interaction security
