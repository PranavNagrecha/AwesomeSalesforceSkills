# LLM Anti-Patterns — HIPAA Workflow Design

Common mistakes AI coding assistants make when generating or advising on HIPAA workflow design in Salesforce.

## Anti-Pattern 1: Recommending Standard Field History Tracking for HIPAA Audit

**What the LLM generates:** Instructions to enable standard Field History Tracking on PHI fields and present it as the HIPAA audit trail solution, without noting the 18-month retention limitation.

**Why it happens:** Standard Field History Tracking is the default Salesforce audit feature with extensive training data. LLMs recommend it without knowing the HIPAA-specific retention requirement (6 years) or the retention limitation of the standard feature (18 months).

**Correct pattern:**
With Field Audit Trail (a Shield feature), archived field history is kept until you delete it, and up to 200 fields per object can be tracked; without it, history lasts 18 months (24 via API) on up to 20 fields. Choose Field Audit Trail when the agreed retention period exceeds 18 months, and write a deletion procedure, because nothing is deleted automatically. Earlier versions of this skill said "up to 10-year retention"; the Summer '26 Security Guide says until deleted. UNVERIFIED (2026-10-03): the 6-year HIPAA figure is a regulatory interpretation for counsel.

**Detection hint:** If the recommended audit trail solution mentions "Field History Tracking" without "Shield" or without noting the 18-month retention limit, it is applying the wrong control.

---

## Anti-Pattern 2: Omitting Event Monitoring SIEM Streaming Requirement

**What the LLM generates:** Recommendations to enable Event Monitoring as a HIPAA access audit control without any plan for retention beyond the platform window, or with a wrong window ("logs expire after 30 days").

**Why it happens:** "Enable Event Monitoring" is the correct first step, and retention differs by source, so the model picks one number. Event Log File storage is 1 year by default for Shield and Event Monitoring customers; real-time streaming events are kept up to 3 days; Event Log Objects up to 30 days.

**Correct pattern:**
Export Event Log Files to an external store (a SIEM or archive) well before the one-year window ends, subscribe to real-time events if near-real-time alerting is needed, and monitor the export. Set the external retention period from counsel's interpretation of HIPAA (UNVERIFIED (2026-10-03): the 6-year figure).

**Detection hint:** If the HIPAA compliance recommendation includes Event Monitoring without mentioning SIEM streaming and 6-year retention, the long-term retention requirement is missing.

---

## Anti-Pattern 3: Assuming BAA Covers All Org Products

**What the LLM generates:** Claims that signing the Salesforce BAA provides HIPAA coverage for all features and products used in the org, including AppExchange packages and all Salesforce cloud products.

**Why it happens:** The concept of a single Business Associate Agreement covering a vendor is intuitive. The nuance that Salesforce's BAA covers specific named products rather than all services is a commercial/legal detail not inferrable from general HIPAA knowledge.

**Correct pattern:**
The Salesforce BAA covers specific enumerated products. AppExchange managed packages are generally NOT covered by the Salesforce BAA. Multi-cloud orgs must verify BAA coverage for every product that may process or store PHI. Some products (e.g., Marketing Cloud) require separate BAA addenda.

**Detection hint:** If the compliance guidance states or implies that the Salesforce BAA covers everything in the org without verification, the product-specific coverage nuance is missing.

UNVERIFIED (2026-10-03): BAA scope and environment coverage are contractual terms; neither the BAA nor its coverage list was read for this pass. Confirm with the Salesforce account team and counsel.

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

UNVERIFIED (2026-10-03): BAA scope and environment coverage are contractual terms; neither the BAA nor its coverage list was read for this pass. Confirm with the Salesforce account team and counsel.

---

## Anti-Pattern 6: Assuming Every PHI Field Can Be History-Tracked

**What the LLM generates:** "Enable field history on all PHI fields, including clinical notes," as if that covers every change.

**Why it happens:** The model assumes history tracking is available on every field type.

**Correct pattern:** Field history cannot track long text fields, multi-select fields, formula, roll-up summary, or auto-number fields, or Created By and Last Modified By. List untrackable PHI fields and specify alternative evidence (versioned child records, an audit object written by automation).

**Detection hint:** A history plan that includes a long text or multi-select PHI field with no alternative evidence.

---

## Anti-Pattern 7: Turning On Encryption and Assuming the Archive Is Encrypted

**What the LLM generates:** "After enabling Shield Platform Encryption on PHI fields, all copies of the data, including history, are encrypted."

**Why it happens:** Encryption at rest sounds global.

**Correct pattern:** "If you turn on Platform Encryption, the previously archived data remains unencrypted." Enable encryption before history is archived, or request re-encryption and re-archiving from Salesforce and delete the unencrypted archive.

**Detection hint:** An encryption rollout plan for an org that already uses Field Audit Trail, with no step for archived history.

---

## Anti-Pattern 8: Treating `archiveRetentionYears` as Automatic Deletion

**What the LLM generates:** "Set archiveRetentionYears to 6 and Salesforce will purge the archive after six years."

**Why it happens:** The field name reads like a retention setting with enforcement.

**Correct pattern:** `archiveRetentionYears` is "the number of years until you manually delete data from the archive. Use this field as a reminder for manually deleting data. By default, field history data isn't automatically deleted when Field Audit Trail is enabled." Write a manual deletion procedure, and remember that deleting a production record does not delete its archived history.

**Detection hint:** Any statement that the archive deletes itself.

---

## Anti-Pattern 9: Keeping the PHI Inventory Outside the Metadata

**What the LLM generates:** A spreadsheet of PHI fields maintained by hand, with no field-level tags.

**Why it happens:** Inventories are traditionally documents.

**Correct pattern:** Tag each PHI field with `complianceGroup` HIPAA and a `securityClassification` in its `CustomField` definition, and check the tags in code review, so the inventory changes whenever the schema does.

**Detection hint:** A PHI field deploy without `complianceGroup`.

