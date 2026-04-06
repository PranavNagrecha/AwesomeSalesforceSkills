# LLM Anti-Patterns — Einstein Trust Layer

Common mistakes AI coding assistants make when generating or advising on Einstein Trust Layer configuration.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Assuming Zero Data Retention Means Data Never Leaves Salesforce

**What the LLM generates:** "Enable Zero Data Retention (ZDR) and your data stays within Salesforce" — implying the data is never sent to an external LLM provider. ZDR means the external provider does not RETAIN the data after processing, not that the data is never transmitted.

**Why it happens:** The name "Zero Data Retention" is interpreted literally by LLMs as "zero data exposure." In reality, the prompt (including grounded record data) IS sent to the external LLM for inference. ZDR is a contractual and technical agreement that the provider processes and discards the data without storing it for training or future use.

**Correct pattern:**

```text
Zero Data Retention (ZDR) — what it actually means:

Data flow with ZDR enabled:
1. Salesforce constructs the prompt (may include record data)
2. Trust Layer applies data masking (PII fields masked)
3. Masked prompt is SENT to the external LLM provider
4. LLM processes the prompt and returns a response
5. Provider discards the prompt and response (no storage, no training)
6. Trust Layer de-masks the response and returns to user

What ZDR guarantees:
- Provider does not store prompts or responses
- Provider does not use your data for model training
- Data is processed in-memory and discarded

What ZDR does NOT guarantee:
- Data never leaves Salesforce (it does, for inference)
- Data is encrypted in transit only by ZDR (TLS handles this separately)
- Compliance with all data residency regulations
  (data may cross geographic boundaries during inference)

For strict data residency:
- Use Salesforce-hosted models (no external transmission)
- Or use BYOLLM with a provider in your required region
- ZDR alone does not satisfy EU data residency requirements
  if the LLM provider processes in the US
```

**Detection hint:** Flag ZDR descriptions that claim data never leaves Salesforce. Check for compliance documentation that relies solely on ZDR for data residency. Flag missing data masking configuration alongside ZDR.

---

## Anti-Pattern 2: Not Configuring Data Masking for Sensitive Fields

**What the LLM generates:** "The Trust Layer automatically masks PII before sending to the LLM" without noting that data masking must be explicitly configured — you must specify which fields and data patterns to mask, and the default configuration may not cover all sensitive fields in your org.

**Why it happens:** LLMs present Trust Layer data masking as automatic and complete. In practice, masking requires configuration: enabling masking, selecting masking rules, and verifying that custom fields containing PII are covered.

**Correct pattern:**

```text
Trust Layer data masking configuration:

Default masking:
- Salesforce provides default masking patterns for common PII
  (SSN, credit card numbers, phone numbers, email addresses)
- Default patterns use regex-based detection

What defaults may miss:
- Custom fields containing PII (e.g., Passport_Number__c)
- Free-text fields with embedded PII (e.g., Case Description
  containing "My SSN is 123-45-6789")
- Non-US PII formats (e.g., UK National Insurance numbers)
- Industry-specific sensitive data (medical record numbers,
  student IDs, financial account numbers)

Configuration steps:
1. Setup > Einstein Trust Layer > Data Masking
2. Review default masking rules
3. Add custom masking rules for org-specific PII fields
4. Test masking with sample prompts in the Prompt Builder
5. Monitor the audit trail for unmasked PII in prompts

Masking behavior:
- Masked values are replaced with tokens before LLM transmission
- Tokens are de-masked in the response
- Masking applies to the prompt, not to the response generation
  (the LLM does not see the original value)

Test rigorously: create test cases with known PII in various
field locations and verify masking in the audit trail.
```

**Detection hint:** Flag Trust Layer setups that rely solely on default masking without custom rule review. Check for orgs with custom PII fields not covered by masking rules. Flag missing masking test verification.

---

## Anti-Pattern 3: Disabling Toxicity Detection to Fix Blocked Responses

**What the LLM generates:** "If the Trust Layer is blocking valid responses, disable toxicity detection" as a troubleshooting step, without noting that toxicity detection is a safety control that should be tuned, not disabled.

**Why it happens:** Toxicity detection can produce false positives — blocking legitimate business content that contains medical terms, legal language, or industry jargon that triggers the toxicity classifier. LLMs suggest the simplest fix: disable the control.

**Correct pattern:**

```text
Toxicity detection tuning (not disabling):

When legitimate responses are blocked:
1. Check the audit trail for the specific toxicity category triggered
   (hate speech, violence, sexual content, self-harm, etc.)
2. Identify the content that triggered the detection
3. Determine if it is a false positive (medical term, legal language)

Resolution options (in order of preference):
1. Adjust the toxicity threshold (less aggressive filtering)
   - Lower the sensitivity for specific categories
   - Keep high sensitivity for clearly inappropriate content

2. Add domain-specific exceptions
   - Medical orgs: allow clinical terminology
   - Legal orgs: allow legal case descriptions
   - Financial orgs: allow fraud investigation language

3. Modify the prompt template to avoid triggering content
   - Rephrase instructions that cause the model to generate
     content flagged by the toxicity detector

4. LAST RESORT: disable specific toxicity categories
   - Only after documented review and approval
   - Never disable ALL toxicity detection
   - Document the business justification

Never disable toxicity detection globally.
It is a safety net, not a nuisance.
```

**Detection hint:** Flag advice to disable toxicity detection entirely. Check for orgs with toxicity detection disabled without documented justification. Flag missing threshold tuning before disabling.

---

## Anti-Pattern 4: Not Enabling or Reviewing the AI Audit Trail

**What the LLM generates:** "Configure the Trust Layer for security" without mentioning the audit trail — the log of all AI interactions showing prompts sent, responses received, masking applied, and toxicity scores. The audit trail is critical for compliance, debugging, and monitoring.

**Why it happens:** Audit trails are operational concerns, not configuration features. LLMs focus on setting up the generative AI capability and skip the observability layer that makes it auditable.

**Correct pattern:**

```text
Einstein Trust Layer audit trail:

What is logged:
- Full prompt text (after masking)
- Full response text
- Masking events (which fields were masked, what patterns matched)
- Toxicity scores per category
- Model used (standard or BYOLLM)
- Timestamp and user who triggered the interaction
- Token consumption

Enablement:
1. Setup > Einstein Trust Layer > Audit Trail
2. Verify logging is active for all Einstein features in scope
3. Set retention period per compliance requirements

Usage:
- Compliance review: prove that PII was masked before transmission
- Debugging: inspect the actual prompt sent for incorrect responses
- Monitoring: track token usage, toxicity trigger rates, error rates
- Cost management: identify high-volume prompt patterns

Access control:
- Restrict audit trail access to compliance and admin roles
- The audit trail itself contains sensitive data (masked prompts
  still show context; responses may contain generated PII)
- Do NOT grant audit trail access to all Einstein users

Review cadence:
- Weekly: check for toxicity false positives
- Monthly: review masking coverage for new fields
- Quarterly: compliance audit of AI interaction logs
```

**Detection hint:** Flag Trust Layer configurations that do not mention the audit trail. Check for orgs with Einstein generative AI active but no audit trail enabled. Flag missing access controls on audit trail data.

---

## Anti-Pattern 5: Treating the Trust Layer as Optional for Agentforce Deployments

**What the LLM generates:** Agentforce agent creation and deployment guides that do not mention configuring the Trust Layer, treating it as a separate nice-to-have security feature rather than an integral part of the Agentforce architecture.

**Why it happens:** Trust Layer documentation is separate from Agentforce agent setup documentation. LLMs treat them as independent features. In practice, every Agentforce interaction flows through the Trust Layer — if it is not configured, default settings apply, which may not meet the organization's security requirements.

**Correct pattern:**

```text
Trust Layer is not optional for Agentforce:

Every Agentforce interaction flows through the Trust Layer:
  User utterance → Topic routing → Action execution →
  Prompt construction → TRUST LAYER → LLM → TRUST LAYER → Response

Trust Layer controls that affect Agentforce:
1. Data masking: PII in grounded record data is masked before
   the agent's prompt reaches the LLM
2. Toxicity detection: agent responses are checked before
   being displayed to the user
3. Grounding: controls what retrieved data is included in prompts
4. Audit trail: logs every agent-user interaction for compliance
5. ZDR: ensures the LLM provider does not retain conversation data

Agentforce deployment checklist (Trust Layer items):
- [ ] Data masking configured for fields used in agent actions
- [ ] Toxicity detection thresholds set for the use case
- [ ] Audit trail enabled and access-controlled
- [ ] ZDR verified with the model provider
- [ ] Grounding controls reviewed (what data reaches the LLM)
- [ ] Model selection reviewed (standard vs BYOLLM)

Skipping Trust Layer configuration means accepting defaults.
Defaults may not match your compliance, security, or privacy requirements.
```

**Detection hint:** Flag Agentforce deployment guides that do not include Trust Layer configuration steps. Check for active agents in orgs where Trust Layer settings are at defaults. Flag missing data masking review for agent-accessible objects.

---
