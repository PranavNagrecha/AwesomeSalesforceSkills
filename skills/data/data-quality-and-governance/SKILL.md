---
name: data-quality-and-governance
description: "Use this skill when designing data quality gates, auditing data quality posture, troubleshooting validation failures, or implementing governance controls (field history, GDPR erasure, data classification, duplicate strategy) across a Salesforce org. Trigger keywords: validation rules, field history, duplicate management, GDPR right to erasure, data retention, data classification, Shield Field Audit Trail, Einstein Data Detect, Matching Rules, PII anonymization. NOT for Duplicate Rules configuration step-by-step UI setup (use duplicate-management skill). NOT for bulk data migration execution (use data-migration skill)."
category: data
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Reliability
  - Operational Excellence
triggers:
  - "How do I enforce required field combinations on an object without making both fields universally mandatory?"
  - "Field history is not capturing changes made during a data migration load — what is going wrong?"
  - "We received a GDPR right-to-erasure request but hard-deleting the contact would break related records"
  - "Duplicate rules are not blocking duplicates when records are inserted via Apex code"
  - "We need to track which fields contain PII and classify them as confidential for compliance audits"
tags:
  - data-quality
  - data-governance
  - validation-rules
  - field-history
  - duplicate-management
  - gdpr
  - data-classification
  - shield
  - pii
inputs:
  - "Object API names requiring data quality controls"
  - "Compliance requirements (GDPR, HIPAA, CCPA, or internal data classification policy)"
  - "List of PII or sensitive fields on each object"
  - "Current Salesforce edition and license (Shield, Duplicate Management, Einstein Data Detect availability)"
  - "Existing validation rule list and any reported bypass complaints from integration teams"
outputs:
  - "Validation rule strategy with Custom Permission-based bypass pattern"
  - "Duplicate Rule + Matching Rule configuration recommendation"
  - "Field history configuration list (up to 20 fields per object)"
  - "GDPR right-to-erasure anonymization pattern and field token map"
  - "Data classification field attribute guidance (Data Sensitivity Level, Compliance Categorization)"
  - "Audit findings: missing bypass conditions, alert-only duplicate rules, objects with no history enabled"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-04
---

# Data Quality and Governance

This skill activates when a practitioner needs to design or audit data quality controls, enforce compliance requirements, or troubleshoot failures in validation, deduplication, or audit trail configuration across a Salesforce org. It covers the full governance stack: validation rules, duplicate management strategy, field history, GDPR/retention patterns, data classification, and Shield-layer controls.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Edition and licenses in play:** Duplicate Management advanced features require a separate license. Shield Field Audit Trail and Einstein Data Detect require the Salesforce Shield add-on. Confirm what the org has before recommending Shield-specific controls.
- **Most common wrong assumption:** Practitioners assume Duplicate Rules block duplicates in all contexts. They do not. Duplicate Rules run in the UI and through standard Salesforce APIs, but Apex DML and Bulk API v1 bypass them unless `Database.DMLOptions.DuplicateRuleHeader` is explicitly set in Apex. Bulk API 2.0 does not support DML options and cannot trigger Duplicate Rules.
- **Field history hard limit:** Each object supports tracking on at most 20 fields. This is a hard platform limit. Choosing which 20 fields to track is a governance decision, not an afterthought.
- **Validation rules fire on API updates:** Every save operation — UI, REST API, Apex, Bulk API — triggers validation rules unless a bypass mechanism is active. Data migrations must plan for this.
- **Cross-object validation rule depth:** Formula-based cross-object checks in validation rules are limited to one relationship level (e.g., `Account.Type` from Opportunity). Deeper traversal is not supported and causes a compile error.

---

## Core Concepts

### Validation Rules as Data Gates

Validation rules are formula-based constraints that prevent a record save when the formula evaluates to `true`. They are the primary declarative mechanism for enforcing data quality at the point of entry.

**Use cases:**
- Required field combinations: enforce that if `Stage = Closed Won` then `Close_Reason__c` must be populated. A simple `AND(ISPICKVAL(StageName, 'Closed Won'), ISBLANK(Close_Reason__c))` achieves this without making the field globally required.
- Conditional logic: require `Billing Country` only when `Account Type = Customer`. Universal required settings cannot express this.
- Cross-field consistency checks: validate that `End_Date__c >= Start_Date__c` using `End_Date__c < Start_Date__c`.
- Cross-object formula restrictions: check a parent field via relationship traversal — e.g., prevent creating a Contact under an inactive Account with `Account.Active__c = false` (one level only).

**Custom Permission-based bypass:** For integrations and data migrations that must bypass validation rules legitimately, the pattern is:
1. Create a Custom Permission (e.g., `Bypass_Validation_Rules`).
2. Wrap every validation rule formula with `AND(NOT($Permission.Bypass_Validation_Rules), <original formula>)`.
3. Assign the Custom Permission to a Permission Set used only by integration users.

This is preferable to System Administrator profile bypasses (which are role-based and too broad) and to `$Profile.Name` checks (which are brittle and hard to audit).

### Duplicate Management Strategy

Salesforce Duplicate Management has two components: **Matching Rules** (define what constitutes a duplicate) and **Duplicate Rules** (define what to do when a match is found).

**Matching Rules:**
- Standard rules ship for Account, Contact, and Lead and use a combination of exact and fuzzy matching on key fields (name, email, phone, address).
- Custom rules allow field-by-field match logic including exact, fuzzy (string similarity), or phone/email-specific methods.
- Fuzzy matching is available in standard rules but is computationally heavier. For large volumes, this can affect save performance.

**Duplicate Rules — alert vs block:**
- Alert mode: shows the duplicate warning but allows the save to proceed. Appropriate for low-stakes objects or user-managed decisions.
- Block mode: prevents the save entirely. Appropriate for critical objects like Account and Contact where duplicate proliferation causes downstream integrity problems.
- Report mode: logs duplicate encounters to a Duplicate Record Set for review without interrupting the user.

**When standard Duplicate Rules are not enough:**
- Cross-object duplicate detection (e.g., matching a Lead against existing Contacts) is supported by standard rules but has limits.
- For large-volume deduplication of existing data (millions of records), third-party dedupe apps (e.g., Cloudingo, DemandTools) are needed. Standard Duplicate Rules do not run retroactively on existing data.
- Apex-driven deduplication via `Database.findDuplicates()` is available and supports programmatic duplicate detection without a UI save event.

**Apex and Bulk API bypass (critical):**
- Apex DML does not trigger Duplicate Rules by default. To enable checking: set `Database.DMLOptions.DuplicateRuleHeader.allowSave = false` on the DML options before the insert/update.
- Bulk API 2.0 cannot trigger Duplicate Rules at all. Bulk loads must run deduplication as a separate pre- or post-load step.

### Field History as Audit Trail

Field history tracking records every change to a tracked field — who changed it, when, from what value, to what value. Changes are stored in the associated `XxxHistory` sObject (e.g., `AccountHistory`, `OpportunityFieldHistory`).

**Key limits and behaviors:**
- Hard limit: 20 fields per object can be tracked simultaneously.
- Retention: standard field history is retained for 18 months rolling. Records older than 18 months are automatically deleted by Salesforce.
- Shield Field Audit Trail: with the Shield add-on, history can be retained for up to 10 years and is queryable via SOQL on the `FieldHistoryArchive` object.
- Which fields are trackable: most field types are supported. The following are NOT trackable: encrypted fields (Classic Encryption), formula fields, auto-number fields, roll-up summary fields, and some system fields (e.g., `CreatedDate`, `LastModifiedDate` — these are already system-managed).
- First-value behavior: field history does NOT record the initial value set when a record is created. The first history entry appears only after the first edit post-creation. This is a platform behavior, not a bug.

**Querying field history:**
```soql
SELECT Field, OldValue, NewValue, CreatedById, CreatedDate
FROM AccountHistory
WHERE AccountId = '001...'
ORDER BY CreatedDate DESC
```

### GDPR and Data Retention

**Right to erasure:** Salesforce recommends data anonymization rather than hard deletion. Hard deletion of a Contact or Account that has related records (Opportunities, Cases, Activities) will fail due to referential integrity or cause orphaned records. The recommended pattern is:
1. Receive erasure request.
2. Replace PII field values with non-reversible tokens (e.g., `ERASED-<UniqueId>` or a UUID).
3. Clear or tokenize: First Name, Last Name, Email, Phone, Address fields.
4. Soft-delete the record if no related records exist, or leave it with tokenized values if related records must be preserved.
5. Log the erasure event in a custom `Data_Erasure_Log__c` object for compliance audit.

**Retention periods:** Salesforce does not enforce custom data retention periods natively. Implement retention enforcement via:
- Scheduled Apex batch jobs that identify records past retention cutoff and either archive or anonymize them.
- Flow scheduled paths (for simpler, lower-volume cases).
- A custom `Retention_Expires__c` date field set at record creation, queried by the batch.

**Data classification using field attributes:** Salesforce metadata supports the following attributes on field definitions (available in Enterprise Edition and above with Data Classification metadata):
- `Data Sensitivity Level`: values are `Public`, `Internal`, `Confidential`, `Restricted`. Set in Setup > Fields or in field metadata XML.
- `Compliance Categorization`: free-form or picklist field to tag regulatory applicability (e.g., `GDPR`, `HIPAA`, `PCI-DSS`).
These attributes are metadata-only — they do not enforce access control. They are used for discovery, reporting, and governance tooling.

**Einstein Data Detect (Shield):** Available with the Salesforce Shield add-on. Scans existing org data to automatically identify fields that contain PII patterns (email addresses, SSNs, phone numbers, credit card numbers) and recommends classification. Use this to bootstrap a PII field inventory on an existing org.

**Salesforce Shield Platform Encryption:** Encrypts field values at rest using Salesforce-managed or customer-managed keys (Bring Your Own Key / BYOK). Encrypts: specific standard fields and all custom fields designated as Encrypted. Key behaviors:
- Encrypted fields are not searchable via standard SOQL `LIKE` or full-text search — only deterministic encryption (a Shield sub-feature) enables exact-match SOQL.
- Encrypted fields cannot be used in formula fields, roll-up summaries, or default field values.
- Encryption does not replace field-level security (FLS) — both layers should be applied for sensitive fields.
- Field-level masking (visible asterisks in UI) is a separate, simpler feature that does not encrypt the stored value.

---

## Common Patterns

### Mode 1: Designing Data Quality Gates for a New Org or Object

**When to use:** Starting fresh — new object, new org, or onboarding a new business process. Goal is to build quality controls before bad data accumulates.

**How it works:**
1. Identify all fields that have conditional-required or format constraints. Map them to validation rule formulas before any record is created.
2. Implement Custom Permission bypass from day one. Do not wait for an integration to complain.
3. Select the 20 most audit-critical fields for field history tracking. Prioritize: status/stage fields, owner fields, financial amount fields, compliance-relevant date fields.
4. Set `Data Sensitivity Level` and `Compliance Categorization` on all PII fields in field metadata.
5. Create a Duplicate Rule in Block mode for the primary object (Account, Contact) from the start. Alert mode can be used initially but should be upgraded to Block after a validation period.
6. Define a `Retention_Expires__c` date formula or trigger-set field for any object subject to a data retention policy.

**Why not skip it:** Retrofitting validation rules into a mature org is painful because existing data violates new rules. Adding field history after millions of records exist provides no history of past changes. Starting clean is dramatically cheaper.

### Mode 2: Auditing Existing Data Quality Posture

**When to use:** Taking over an existing org, preparing for a compliance audit, or responding to a data quality incident.

**How it works:**
1. Run `scripts/check_data_quality.py --manifest-dir <metadata_dir>` against the unpackaged org metadata to identify: validation rules without Custom Permission bypass, objects with fewer than the expected number of history-tracked fields, Duplicate Rules in alert-only mode on critical objects.
2. Export the field inventory and cross-reference against the PII field register. Identify unclassified fields.
3. Query `XxxHistory` objects for your top 5 critical objects to confirm history is actually capturing changes (a zero-row result on an active object is a red flag).
4. Review Duplicate Record Sets (`DuplicateRecordSet` and `DuplicateRecordItem` objects) to understand the current duplicate backlog.
5. If Shield is licensed, run Einstein Data Detect to surface unregistered PII.

**Output:** A gap report covering: missing bypass conditions, unclassified PII fields, history tracking gaps, duplicate rule coverage gaps.

### Mode 3: Troubleshooting Data Quality Failures

**When to use:** A specific validation rule is firing unexpectedly, field history is not capturing changes, or duplicates are getting through.

**Decision tree:**

| Symptom | Likely Cause | Fix |
|---|---|---|
| Validation rule fires during migration load | No bypass mechanism; rule fires on API updates | Add Custom Permission bypass; grant to integration user |
| Field history not recording change | Field type not trackable (formula, encrypted, auto-number) | Switch to a trackable field type or use a trigger to log changes manually |
| Field history not recording first value | Platform behavior — first value on create is not logged | Accepted behavior; use Apex trigger on `insert` to log initial value to custom audit object if needed |
| Duplicate rule not blocking in Apex | `DMLOptions.DuplicateRuleHeader` not set | Set `dmlOptions.DuplicateRuleHeader.allowSave = false` before DML |
| Duplicate rule not blocking in Bulk API 2.0 | Bulk API 2.0 cannot trigger Duplicate Rules | Run deduplication as a separate pre-load step |
| Duplicate rule in alert mode letting duplicates through | Rule is configured as Alert, not Block | Change rule action to Block; communicate change to users |

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Field required only under specific conditions | Validation rule with conditional formula | Required field setting is binary — cannot express conditional requirements |
| Integration needs to bypass validation rules | Custom Permission + NOT($Permission.X) wrap | Profile-based or user-based bypasses are too broad and non-auditable |
| New org, need to block duplicates from day one | Duplicate Rule in Block mode + standard Matching Rule | Alert mode creates false confidence and duplicate backlog immediately |
| Large-volume deduplication of existing records | Third-party dedupe app (Cloudingo, DemandTools) | Standard Duplicate Rules do not run retroactively |
| Need 10-year audit trail | Shield Field Audit Trail | Standard field history only retains 18 months |
| GDPR erasure request received | Anonymize PII fields (tokenize), do not hard delete | Hard delete breaks referential integrity on related records |
| Want to discover PII fields in existing org | Einstein Data Detect (requires Shield) | Manual field inventory misses fields; automated scanning is more complete |
| Need to encrypt PII at rest | Shield Platform Encryption | Field-level masking does not encrypt stored values |
| Compliance audit requires field classification | Set Data Sensitivity Level + Compliance Categorization on field metadata | Native metadata attributes; no custom objects required |

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

Run through these before marking data quality or governance work complete:

- [ ] All validation rules with conditional requirements include a Custom Permission bypass wrapped in `NOT($Permission.X)`
- [ ] Field history is enabled and 20-field limit is not exceeded on any targeted object
- [ ] Duplicate Rules on Account and Contact are in Block mode (not alert-only) for production
- [ ] PII fields have `Data Sensitivity Level` and `Compliance Categorization` metadata set
- [ ] A GDPR erasure runbook exists and has been tested on a sandbox record (tokenization pattern, not hard delete)
- [ ] Data retention policy is enforced by a scheduled batch or flow, with `Retention_Expires__c` field populated at record creation
- [ ] Shield Platform Encryption is confirmed to not conflict with formula fields, roll-ups, or search needs on encrypted fields
- [ ] Duplicate Rules are tested with an Apex DML scenario to confirm `DMLOptions.DuplicateRuleHeader` is set where needed
- [ ] Field history first-value gap is documented and addressed (trigger-based audit if initial value is compliance-critical)
- [ ] `check_data_quality.py` audit script has been run against org metadata and all issues resolved

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Validation rules fire on every API save** — There is no "UI only" mode for a validation rule. Every REST API call, Apex DML operation, Bulk API job, and Flow-initiated save that modifies the fields in scope will trigger the rule. Data migration jobs that skip bypass setup fail at scale.

2. **Field history does not capture the initial record creation value** — The first entry in `XxxHistory` appears only after the field is edited after creation. If a record is created with `Status = New` and never edited, there is no history row. For compliance use cases where the initial value is audit-critical, a trigger on `insert` must write to a custom audit object.

3. **Duplicate Rules are skipped in Apex DML by default** — Inserting or updating records via Apex bypasses Duplicate Rules unless `Database.DMLOptions.DuplicateRuleHeader.allowSave = false` is set before the operation. This is not a widely known default and causes silent data quality failures in orgs that rely on Duplicate Rules for integrity.

4. **Bulk API 2.0 cannot trigger Duplicate Rules at all** — Unlike Bulk API v1 (which has some limited Duplicate Rule support), Bulk API 2.0 does not support `DMLOptions` and will not check for duplicates regardless of configuration. Any Bulk API 2.0 load must use a pre-load deduplication step.

5. **Shield Platform Encryption breaks SOQL LIKE searches** — Fields encrypted with probabilistic encryption (the default) cannot be searched using `LIKE`, wildcards, or full-text search (SOSL). Switching to deterministic encryption enables exact-match SOQL but has its own security trade-offs (deterministic ciphertext is vulnerable to frequency analysis). Plan encryption choices before enabling, not after.

6. **Cross-object validation rules are limited to one relationship level** — A validation rule on Opportunity can reference `Account.Type` but cannot reference `Account.Parent.Type`. Attempts to traverse two levels result in a compile error. For deeper checks, use Apex triggers.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Validation rule audit report | List of all validation rules with bypass status, formula complexity rating, and API-safe flag |
| Duplicate rule coverage matrix | Object-by-object table of Matching Rule and Duplicate Rule configuration, mode (alert/block/report), and API DML coverage |
| Field history configuration list | Per-object table of history-tracked fields (up to 20), retention tier (18-month vs Shield 10-year), and first-value gap flag |
| PII field register | Field-level inventory with Data Sensitivity Level, Compliance Categorization, and encryption status |
| GDPR erasure runbook | Step-by-step process for receiving, executing, and logging a right-to-erasure request with tokenization map |
| Data retention enforcement design | Batch job or Flow design for enforcing retention cutoffs, with `Retention_Expires__c` field configuration |
| `check_data_quality.py` audit output | Machine-readable issue list from static metadata analysis |

---

## Related Skills

- duplicate-management — Step-by-step configuration of Duplicate Rules and Matching Rules in the Salesforce UI; use alongside this skill when the governance strategy calls for configuring or modifying Duplicate Rules
- data-migration — Bulk data movement execution and DML strategy; field history bypass and validation rule bypass during migration loads are covered here
- security-field-level-security — FLS and profile/permission set configuration for restricting field access; complements Shield encryption for sensitive field protection
