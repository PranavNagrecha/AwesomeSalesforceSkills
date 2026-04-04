# Well-Architected Notes — Data Quality and Governance

## Relevant Pillars

- **Security** — Data governance is fundamentally a security concern. PII classification, Shield Platform Encryption, and field-level access controls work together to protect sensitive data at rest and in transit. Right-to-erasure processes must be auditable and tamper-resistant. Data Sensitivity Level metadata drives the security review agenda for each field. Encryption key management (BYOK) adds operational security complexity that must be planned for.

- **Reliability** — Validation rules are a reliability mechanism: they prevent corrupt or incomplete records from entering the system and causing downstream processing failures. Poorly designed validation rules (missing bypass conditions, overly broad logic) are themselves a reliability risk — they can block legitimate API integrations and bulk loads at scale. Duplicate management prevents the data integrity degradation that accumulates into a systemic reliability problem.

- **Operational Excellence** — Field history and audit trail configuration directly enable operational observability. Without field history on key status and owner fields, incident investigations cannot reconstruct what happened to a record. Retention enforcement automation (scheduled batch, Flow) is an operational process that must be owned, monitored, and alerted on. GDPR erasure runbooks are operational procedures that must be tested, versioned, and handed off to operations teams.

- **Performance** — Fuzzy matching in Duplicate Rules adds computational overhead to every save event on matched objects. On high-volume transactional objects (Leads, Cases) the performance impact of broad fuzzy matching can be significant. Standard field history tracking does not degrade save performance meaningfully, but `FieldHistoryArchive` queries against years of Shield data at scale benefit from selective filtering.

- **Scalability** — Standard Duplicate Rules do not scale for retroactive deduplication of millions of existing records. Validation rules with complex cross-object formulas add query overhead to every save. Shield Field Audit Trail is designed for long-term, high-volume history storage and scales where standard field history does not.

---

## Architectural Tradeoffs

**Validation rule bypass breadth vs security:** The Custom Permission bypass pattern is the right choice, but the scope of the bypass must be as narrow as possible. A single `Bypass_Validation_Rules` permission that bypasses all rules is easy to implement but risky — it gives any user with that permission a blanket exemption. For high-security orgs, consider per-rule Custom Permissions (e.g., `Bypass_VR_Opportunity_CloseReason`) to allow surgical bypass. The cost is more permissions to manage; the benefit is finer control.

**Block mode Duplicate Rules vs user experience:** Block mode prevents duplicate creation entirely but generates friction for users who receive false positives (the matching rule flags a record that is not truly a duplicate). Poorly tuned Matching Rules in Block mode cause productivity losses and Help Desk tickets. The tradeoff is data integrity vs user experience. The correct answer is to tune Matching Rules carefully before switching from Alert to Block, not to keep Alert mode indefinitely to avoid tuning work.

**Shield encryption vs search capability:** Encrypting PII fields removes search-by-content capability. For fields like Email and Phone that are frequently used in search-driven workflows (customer lookup, deduplication), this is a significant operational cost. Deterministic encryption restores exact-match SOQL but has different security properties. This tradeoff must be made explicitly, documented in the data classification register, and accepted by security and operations jointly — not decided unilaterally by a developer.

**18-month standard retention vs Shield Field Audit Trail cost:** Shield Field Audit Trail is a licensed add-on with additional cost. For regulated industries (financial services, healthcare) where 7–10 year retention is mandatory, Shield is the only native solution. For non-regulated orgs where 18 months is sufficient, standard field history is free and adequate. Do not recommend Shield purely for history retention unless the business case justifies the license cost.

**GDPR anonymization vs record deletion:** Anonymization preserves referential integrity at the cost of keeping a "ghost" record in the system. Hard deletion is cleaner but breaks related records and can cause report totals to change unexpectedly. Anonymization is the Salesforce-recommended pattern and is the right default. The exception is when the Contact has zero related records — in that case, deletion is cleaner and acceptable.

---

## Anti-Patterns

1. **Using System Administrator profile as the validation rule bypass** — Configuring `$Profile.Name = 'System Administrator'` as the bypass condition is common but dangerous. Every System Administrator in the org permanently bypasses all validation rules, including during normal day-to-day use. An admin who edits a record in the UI without realizing they are bypassing a rule can corrupt data silently. Use Custom Permissions with a dedicated Permission Set instead — assign and revoke explicitly, and only for the duration of the operation that requires bypass.

2. **Tracking formula fields in field history expecting to see calculated value changes** — Formula fields are not trackable and the platform does not throw an error when you attempt to enable tracking on them — it simply ignores the configuration. Teams spend hours debugging missing history rows before discovering the root cause. Track the source fields that drive the formula instead.

3. **Relying on Duplicate Rules as the sole protection against duplicates in Apex and integration contexts** — Duplicate Rules are a UI and standard API control. They are bypassed by Apex DML (by default) and by Bulk API 2.0 (always). An architecture that assumes Duplicate Rules prevent all duplicates is silently broken for all programmatic data paths. Every Apex insert or update that creates records must explicitly set `DMLOptions.DuplicateRuleHeader` if duplicate prevention is required.

4. **Treating Data Sensitivity Level as an enforcement control** — Marking a field as `Restricted` in the data classification metadata creates no access control. The attribute is a label, not a lock. Orgs that treat classification as equivalent to protection leave sensitive fields fully readable by anyone with object-level access, while believing they have "restricted" the data.

5. **Leaving GDPR erasure to manual, ad-hoc processes** — Erasure requests handled manually without a documented runbook, a custom logging object, and a tested anonymization script are a compliance liability. Missing a field during manual anonymization (e.g., `Description` field containing a phone number) leaves PII in the record. Automated, script-driven erasure with a mandatory log entry is the only auditable approach.

---

## Official Sources Used

- Salesforce Help — Using Field History Tracking: https://help.salesforce.com/s/articleView?id=sf.fields_using_field_history.htm
- Salesforce Help — Duplicate Rules Map of Tasks: https://help.salesforce.com/s/articleView?id=sf.duplicate_rules_map_of_tasks.htm
- Salesforce Help — Shield Platform Encryption Overview: https://help.salesforce.com/s/articleView?id=sf.security_pe_overview.htm
- Apex Developer Guide — Database DML Options (DuplicateRuleHeader): https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/langCon_apex_dml_database_dml_options.htm
- Salesforce Well-Architected Overview — architecture quality model and pillar framing: https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
