# LLM Anti-Patterns — HIPAA Workflow Design

Common mistakes AI coding assistants make when generating or advising on HIPAA workflow design in Salesforce.

## Anti-Pattern 1: Recommending Standard Field History Tracking for HIPAA Audit

**What the LLM generates:** Instructions to enable standard Field History Tracking on PHI fields and present it as the HIPAA audit trail solution, without noting the 18-month retention limitation.

**Why it happens:** Standard Field History Tracking is the default Salesforce audit feature with extensive training data. LLMs recommend it without knowing the HIPAA-specific retention requirement (6 years) or the retention limitation of the standard feature (18 months).

**Correct pattern:**
Shield Field Audit Trail (paid add-on) provides up to 10-year retention and is the only Salesforce feature that satisfies HIPAA's 6-year audit log retention requirement. Standard Field History Tracking must NOT be used as the primary audit mechanism for PHI fields.

**Detection hint:** If the recommended audit trail solution mentions "Field History Tracking" without "Shield" or without noting the 18-month retention limit, it is applying the wrong control.

---

## Anti-Pattern 2: Omitting Event Monitoring SIEM Streaming Requirement

**What the LLM generates:** Recommendations to enable Event Monitoring as a HIPAA access audit control, without noting that Event Monitoring logs expire after 30 days or that streaming to a SIEM is required for 6-year retention.

**Why it happens:** "Enable Event Monitoring" is the correct first step. LLMs stop there without knowing that Salesforce does not retain logs beyond 30 days and that the customer is responsible for long-term retention via external streaming.

**Correct pattern:**
Event Monitoring must be combined with a SIEM streaming pipeline that streams logs daily (before the 30-day expiration). The SIEM must retain logs for at least 6 years. The streaming pipeline is an ongoing operational requirement, not a one-time setup.

**Detection hint:** If the HIPAA compliance recommendation includes Event Monitoring without mentioning SIEM streaming and 6-year retention, the long-term retention requirement is missing.

---

## Anti-Pattern 3: Assuming BAA Covers All Org Products

**What the LLM generates:** Claims that signing the Salesforce BAA provides HIPAA coverage for all features and products used in the org, including AppExchange packages and all Salesforce cloud products.

**Why it happens:** The concept of a single Business Associate Agreement covering a vendor is intuitive. The nuance that Salesforce's BAA covers specific named products rather than all services is a commercial/legal detail not inferrable from general HIPAA knowledge.

**Correct pattern:**
The Salesforce BAA covers specific enumerated products. AppExchange managed packages are generally NOT covered by the Salesforce BAA. Multi-cloud orgs must verify BAA coverage for every product that may process or store PHI. Some products (e.g., Marketing Cloud) require separate BAA addenda.

**Detection hint:** If the compliance guidance states or implies that the Salesforce BAA covers everything in the org without verification, the product-specific coverage nuance is missing.

---

## Anti-Pattern 4: Treating Consent Management as Access Control Enforcement

**What the LLM generates:** Architecture that relies on AuthorizationFormConsent records to enforce PHI access restrictions, assuming that unconsented patients' records are automatically restricted.

**Why it happens:** Consent and access control are logically related (you shouldn't access PHI without consent), leading LLMs to conflate the tracking object with enforcement mechanism.

**Correct pattern:**
AuthorizationFormConsent tracks that consent was obtained — it does not enforce record-level access restrictions. PHI access control is implemented via OWD settings, sharing rules, and permission sets, independently of the consent data model. Enrollment workflows must explicitly check consent status and conditionally proceed.

**Detection hint:** If the access control design relies on the presence/absence of AuthorizationFormConsent records to restrict PHI access without separate sharing rule configuration, the access control enforcement gap exists.

---

## Anti-Pattern 5: Storing PHI in Sandboxes Without BAA Coverage

**What the LLM generates:** Test/development workflows that load real patient data (from production or EHR exports) into sandbox environments for testing, without noting that sandboxes require BAA coverage for PHI storage.

**Why it happens:** Development teams routinely use production-like data in sandboxes for realistic testing. LLMs recommend this pattern without knowing that sandbox PHI storage requires the same BAA coverage as production.

**Correct pattern:**
PHI requires BAA coverage in ALL Salesforce environments — sandboxes included. Use fully synthetic (not anonymized or de-identified) test data in sandboxes unless the sandbox environment is explicitly covered under the BAA. Anonymization and pseudonymization of real patient data still leaves re-identification risk and may not satisfy HIPAA de-identification safe harbor standards.

**Detection hint:** If the testing strategy involves copying or importing real patient records into sandbox environments without explicitly confirming BAA sandbox coverage, the PHI storage requirement is being violated.
