# Gotchas — Einstein Trust Layer

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Data Masking Does Not Apply to Agentforce Agents by Default

**What happens:** Administrators enable data masking in Einstein Trust Layer setup, confirm the toggle is On, and select sensitive data categories. They then deploy an Agentforce agent that grounds prompts with customer record data. PII (names, contact details) is sent to the external LLM in plain text — without any masking placeholder substitution — despite masking appearing to be enabled.

**When it occurs:** When the org has data masking enabled at the Trust Layer level but the specific Einstein feature is an Agentforce agent. As of Spring '25, data masking is applied to embedded features (Einstein Service Replies, Einstein Work Summaries, Prompt Builder previews) but is not applied to Agentforce agent prompt pipelines by default. The Trust Layer setup UI does not clearly surface this feature-level distinction.

**How to avoid:** Before assuming masking is active for a given feature, check the current Salesforce release notes for the specific masking coverage matrix. Test agent prompts using Prompt Builder or agent testing tools with known PII records and verify that placeholder tokens appear in the intermediate prompt, not raw values. Track the Salesforce roadmap for expanded agent masking coverage in future releases.

---

## Gotcha 2: Zero Data Retention Does Not Prevent PII Transmission — It Only Governs Post-Processing Storage

**What happens:** A team implements Einstein AI with ZDR in place and communicates to stakeholders that "customer data does not leave Salesforce" or "data is not shared with OpenAI." Both statements are incorrect. The prompt — which may contain PII if data masking is not separately enabled — does travel to OpenAI's enterprise API. ZDR means OpenAI discards it immediately after the response is generated and does not use it for training or store it beyond the API call. The data does leave Salesforce temporarily during the LLM call.

**When it occurs:** Any time practitioners conflate ZDR with data masking, or use ZDR as the justification for not enabling data masking. This causes compliance gaps in regulated industries (healthcare, financial services) where even transient third-party exposure of PII or PHI may require controls or notification obligations.

**How to avoid:** Treat ZDR and data masking as two separate controls with different scope. ZDR governs what the LLM provider retains after processing. Data masking governs what the LLM provider ever sees. Both must be configured for a complete data protection posture. Document this distinction explicitly in your org's AI governance documentation.

---

## Gotcha 3: Invalid-Format PII Is Not Masked — and There Is No Warning

**What happens:** Data masking appears to be working correctly for most records, but specific records with edge-case data formats pass PII through to the LLM unmasked. For example: a phone number stored in an unusual international format, a social security number stored with dashes in a non-standard position, or a credit card number with leading/trailing spaces from a data import. The Trust Layer's masking engine validates format and structure before applying placeholders — invalid-format values do not trigger masking. There is no error, warning, or audit flag when a value fails to be masked.

**When it occurs:** When org data quality is inconsistent — common after data migrations, legacy imports, or integrations that do not enforce format validation. Also occurs with multi-country or cross-region data where the masking model's pattern detection is less reliable.

**How to avoid:** Test data masking with a realistic sample of production-format records, not just clean test data. Include edge cases: international phone formats, SSNs from different countries, names with special characters. Review the Prompt Builder preview output for any unmasked values. Address upstream data quality issues (field validation rules, normalization on import) to ensure the masking engine can detect the fields it is meant to protect.

---

## Gotcha 4: Audit Trail Is Not Retroactive — There Is No Backfill for Interactions Before Enablement

**What happens:** An organization enables Einstein AI features in production, uses them for weeks or months, and then enables the audit trail when a compliance request arrives. The audit trail captures only interactions from the point of enablement forward. All prior interactions are unrecoverable. The compliance team cannot produce records for the period before enablement.

**When it occurs:** When audit trail is treated as an afterthought rather than a prerequisite for production deployment. Also occurs when audit trail is disabled temporarily for troubleshooting and not re-enabled promptly.

**How to avoid:** Treat audit trail enablement as a prerequisite gate before any Einstein AI feature is accessible to production users. Include it in the Trust Layer setup checklist. Confirm the retention period is configured to match your compliance policy (e.g., 1 year, 7 years) before go-live. Monitor the audit trail enablement status as part of org health checks.

---

## Gotcha 5: The 65,536-Token Context Window Applies Only When Data Masking Is Active — Breaking Prompts That Worked Without It

**What happens:** A prompt template is developed, tested, and approved with data masking disabled or in an org without Trust Layer masking active. The template uses extensive dynamic grounding — multiple Data Cloud retrievals, several knowledge articles, and a long system prompt. When data masking is subsequently enabled (as part of a security hardening step), the same prompt starts failing or returning truncated responses. The root cause is that data masking lowers the effective context window from the model's native limit to a hard ceiling of 65,536 tokens, and the fully-grounded prompt exceeds this limit.

**When it occurs:** When data masking is enabled after prompt templates are already designed and tested. Also occurs when dynamic grounding retrieves more records than anticipated at runtime, pushing a borderline prompt over the limit.

**How to avoid:** Design and test all prompt templates with data masking active from the start. Establish a token budget target of 50,000 tokens or less for the fully-grounded prompt to leave headroom for the response. Audit all dynamic grounding retrievals for worst-case token consumption. Trim long text area fields, limit the number of retrieved knowledge articles, and consider pagination patterns for large context requirements.
