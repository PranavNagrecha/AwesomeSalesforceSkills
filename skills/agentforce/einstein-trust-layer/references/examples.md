# Examples — Einstein Trust Layer

## Example 1: Verifying Data Masking Is Active Before Go-Live

**Context:** A service team is preparing to launch Einstein Service Replies in a production org. The feature is configured and tested functionally, but the compliance team has asked for evidence that customer PII (names, phone numbers, case details) is not being sent in plain text to OpenAI.

**Problem:** Without a verification step, practitioners assume that enabling data masking in Setup is sufficient. There is no runtime error if masking is misconfigured — the prompt simply sends unmasked values silently.

**Solution:**

1. In Trust Layer Setup, confirm data masking is toggled On and the following categories are selected: Names, Email Addresses, Phone Numbers (Business and Mobile), Credit Card Numbers.
2. Open Prompt Builder and load a prompt template used by Service Replies.
3. Select a test record that contains known PII values (a test customer with a real-format phone number and name).
4. Use the "Preview" function in Prompt Builder.
5. In the preview output, confirm that the customer name appears as `PERSON_0` and the phone number as `PHONE_0` — not as the raw values.
6. Confirm that the response from the LLM restores the original values in the final output shown to the agent.

```text
Expected masked prompt fragment (sent to LLM):
  "Customer PERSON_0 called about order #12345. Their callback number is PHONE_0."

Expected demasked response fragment (shown to user):
  "Customer Jane Smith called about order #12345. Their callback number is (415) 555-0100."
```

**Why it works:** Prompt Builder's preview mode executes the full Trust Layer pipeline including masking. If placeholders do not appear, data masking is not functioning for that template and must be investigated before production deployment.

---

## Example 2: Using the Audit Trail to Investigate a Compliance Inquiry

**Context:** An internal audit team asks for a log of all AI-generated responses produced for a specific case over the past 30 days, including whether agents accepted or modified those responses.

**Problem:** Without audit trail enabled, there are no interaction-level records. Even with it enabled, practitioners may not know how to locate records in Data 360 or what fields are available.

**Solution:**

1. Confirm audit trail is enabled: Setup > Einstein Setup > Go to Einstein Trust Layer > Audit Trail toggle is On.
2. Navigate to Data 360 and access the Einstein AI interaction dataset.
3. Filter by the date range (last 30 days) and by the case object or feature type (Service Replies).
4. Each interaction record contains:
   - Timestamp of the interaction
   - Original prompt text (including grounded CRM data as sent to the LLM)
   - Toxicity scores by category (composite 0–1 scale)
   - Raw LLM output (before user review)
   - User decision: accepted, rejected, or modified
   - If modified: the final text the user submitted
5. Export or share these records with the audit team as the compliance artifact.

```text
Sample audit record fields:
  interaction_timestamp: 2026-03-15T14:22:31Z
  feature: EinsteinServiceReplies
  toxicity_score_composite: 0.03
  user_decision: modified
  original_llm_output: "I understand your frustration..."
  user_final_output: "I understand your concern and will escalate this immediately."
```

**Why it works:** The audit trail captures the complete interaction lifecycle. The user decision field provides evidence of human oversight, which is often required for AI compliance frameworks.

---

## Example 3: Diagnosing Why a Prompt Fails with Data Masking Active

**Context:** A Prompt Builder template works correctly in preview without data masking, but fails or returns a truncated response when masking is enabled on the org.

**Problem:** Data masking reduces the effective context window to 65,536 tokens. A large prompt template with extensive dynamic grounding (Data Cloud records, knowledge articles) exceeds this limit when masking is active, causing the LLM call to fail silently or return an incomplete response.

**Solution:**

1. Estimate the token count of the fully-grounded prompt at runtime (use a token estimation utility or Prompt Builder's token counter if available).
2. If the grounded prompt exceeds 65,536 tokens, reduce the scope of dynamic grounding — limit the number of knowledge articles retrieved, truncate long text fields, or remove low-value context.
3. Re-test with masking active and verify the response is complete.
4. Document the token budget headroom as part of the prompt template design standards.

```text
Token budget with data masking active:
  Hard limit:  65,536 tokens
  Recommended target: <= 50,000 tokens (leave headroom for response)
  Grounding fields to audit: Long text areas, Knowledge Article bodies, multi-record retrievals
```

**Why it works:** The context window constraint is a hard platform limit when masking is active. Reducing grounding scope is the only remediation — there is no configuration to raise this limit.

---

## Anti-Pattern: Relying on Zero Data Retention as the Sole Data Protection Control

**What practitioners do:** A team enables Einstein AI features, confirms that Salesforce's ZDR agreement with OpenAI is in place, and treats this as sufficient data protection. They do not enable data masking or configure the audit trail.

**What goes wrong:** ZDR means OpenAI does not retain the data after the API call completes. It does not prevent PII from being sent to OpenAI in the first place. Without data masking, customer names, SSNs, phone numbers, and other PII travel to the external LLM in plain text — they are just not stored there afterward. Depending on regulatory requirements (GDPR, HIPAA, PCI-DSS), transmitting PII to a third party even transiently may constitute a violation. Additionally, with no audit trail configured, there is no record of what was sent or received for any compliance review.

**Correct approach:** Treat ZDR, data masking, and the audit trail as three separate and complementary controls. ZDR governs post-processing retention. Data masking governs what the LLM ever sees. The audit trail governs the organization's own visibility into AI interactions. All three should be configured for any production deployment handling sensitive data.
