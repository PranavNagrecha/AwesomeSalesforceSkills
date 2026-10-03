# Examples — Einstein Trust Layer

## Example 1: Verifying Data Masking Is Active Before Go-Live

**Context:** A service team is preparing to launch Einstein Service Replies in a production org. The feature is configured and tested functionally, but the compliance team has asked for evidence that customer PII (names, phone numbers, case details) is not being sent in plain text to OpenAI.

**Problem:** Without a verification step, practitioners assume that enabling data masking in Setup is sufficient. There is no runtime error if masking is misconfigured — the prompt simply sends unmasked values silently.

**Solution:**

1. In Setup, open Einstein Trust Layer and confirm large language model data masking is on (it is on by default) and that Name, Email Address, Phone Number, and Credit Card are selected in the pattern-based list.
2. Open Prompt Builder and load a prompt template used by Service Replies.
3. Select a test record that contains known PII values (a test customer with a real-format phone number and name).
4. Use the Preview function in Prompt Builder.
5. In the resolution, confirm the customer name and phone number appear as placeholder text, and open View Your Data Masking Details to see which placeholder maps to which value.
6. Confirm that the response restores the original values (demasked values are shown in italics).
7. After data collection is on, run the GenAIGatewayRequest report with Timestamp, Model, # promptTokens, Prompt, and MaskedPrompt to confirm the same masking in real traffic.

UNVERIFIED (2026-10-03): the placeholder tokens below illustrate the idea; the guide does not show the exact placeholder format.

```text
Expected masked prompt fragment (sent to LLM):
  "Customer PERSON_0 called about order #12345. Their callback number is PHONE_0."

Expected demasked response fragment (shown to user):
  "Customer Jane Smith called about order #12345. Their callback number is (415) 555-0100."
```

**Why it works:** Prompt Builder's preview mode executes the full Trust Layer pipeline including masking. If placeholders do not appear, data masking is not functioning for that template and must be investigated before production deployment.

---

## Example 2: Using the Audit Trail to Investigate a Compliance Inquiry

**Context:** An internal audit team asks for evidence of what was sent to the LLM for Service Replies over the past 30 days, which responses were flagged for toxicity, and whether agents accepted or modified them.

**Problem:** Earlier versions of this example described an "Audit Trail toggle" and invented field names. The guide's path is different: audit data appears only after Einstein generative AI data collection and storage is turned on and the report package is installed.

**Solution:**

1. Confirm data collection is on in Einstein Setup and the GenAI data streams in Data Cloud show a successful last run.
2. In Data Cloud, Reports tab, create a report from the GenAIGatewayRequest report type. Add Timestamp, Model, # promptTokens, Prompt, and MaskedPrompt. Filter Feature to Service Replies and Timestamp to the last 30 days.
3. Create a second report from GenAIGatewayResponse with GenAIContentCategory. Add Timestamp, ResponseText, DetectorType, Category, and Value. Filter DetectorType equals toxicity.
4. For accept, modify, and reject decisions, use the feedback DMOs (GenAIFeedback `action__c`, GenAIAppGeneration `generationUpdate__c` for the modified text).
5. Export both reports as the compliance artifact, and note that Salesforce also keeps audit and feedback data for 30 days for compliance purposes.

```text
DMO fields used (Field API names from the Data Model for Generative AI Audit and Feedback):
  GenAIGatewayRequest : timestamp__c, feature__c, model__c, provider__c, prompt__c,
                        maskedPrompt__c, enablePiiMasking__c, promptTokens__c,
                        promptTemplateDevName__c, promptTemplateVersionNo__c
  GenAIContentCategory: detectorType__c, category__c, value__c, parent__c
  GenAIFeedback       : action__c, feedback__c, generationId__c, userId__c
```

**Why it works:** The request DMO holds the hydrated and masked prompt side by side, the content category DMO holds detector results by category, and the feedback DMOs hold the human decision.

---

## Example 3: Diagnosing Why a Prompt Fails with Data Masking Active

**Context:** A Prompt Builder template works correctly in preview without data masking, but fails or returns a truncated response when masking is enabled on the org.

**Problem:** Earlier versions said data masking reduces the effective context window to 65,536 tokens. UNVERIFIED (2026-10-03): that figure is not in the Generative AI guide. What the guide does document is that a prompt too large for the model gets an automatic summary in the Resolution panel, and that masking can affect grounding.

**Solution:**

1. Preview the template with masking on and the largest realistic record; check whether the Resolution panel shows an automatic summary.
2. Read `promptTokens__c` for real calls in the GenAIGatewayRequest report, and reduce grounding scope (fewer retrieved articles, shorter long-text fields) where prompts are summarized or responses truncate.
3. Re-test with masking active and verify the response is complete.
4. Document the token budget headroom as part of the prompt template design standards.

```text
Prompt size review:
  Source of truth: promptTokens__c and totalTokens__c in GenAIGatewayRequest
  Signal: automatic summary shown in the Prompt Builder Resolution panel
  Grounding fields to audit: Long text areas, Knowledge Article bodies, multi-record retrievals
```

**Why it works:** Measured token counts from real traffic replace an unverified fixed limit, and the automatic summary is the documented sign that a prompt is too large.

---

## Anti-Pattern: Relying on Zero Data Retention as the Sole Data Protection Control

**What practitioners do:** A team enables Einstein AI features, confirms that Salesforce's ZDR agreement with OpenAI is in place, and treats this as sufficient data protection. They do not enable data masking or configure the audit trail.

**What goes wrong:** ZDR means OpenAI does not retain the data after the API call completes. It does not prevent PII from being sent to OpenAI in the first place. Without data masking, customer names, SSNs, phone numbers, and other PII travel to the external LLM in plain text — they are just not stored there afterward. Depending on regulatory requirements (GDPR, HIPAA, PCI-DSS), transmitting PII to a third party even transiently may constitute a violation. Additionally, with no audit trail configured, there is no record of what was sent or received for any compliance review.

**Correct approach:** Treat ZDR, data masking, and the audit trail as three separate and complementary controls. ZDR governs post-processing retention. Data masking governs what the LLM ever sees. The audit trail governs the organization's own visibility into AI interactions. All three should be configured for any production deployment handling sensitive data.
