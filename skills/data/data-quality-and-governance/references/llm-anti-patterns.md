# LLM Anti-Patterns — Data Quality and Governance

Common mistakes AI coding assistants make when generating or advising on Salesforce data quality and governance controls.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Assuming Duplicate Rules Block All Insertion Channels

**What the LLM generates:** "Enable the Duplicate Rule on Contact to prevent duplicates" without noting that Duplicate Rules only block duplicates created through the UI and standard APIs by default — they do not block records inserted via Apex with `DuplicateRuleHeader` set to `allowSave = true`, or via certain bulk operations unless explicitly configured.

**Why it happens:** Duplicate Rule documentation focuses on UI behavior. LLMs do not distinguish between the different record creation channels (UI, REST API, Apex DML, Data Loader, Flow) and their interaction with duplicate rules.

**Correct pattern:**

```text
Duplicate Rule enforcement by channel:

- UI (Lightning/Classic): enforced by default (alert or block)
- REST/SOAP API: enforced by default, but callers can set
  DuplicateRuleHeader.allowSave = true to bypass
- Apex DML: NOT enforced by default. Must explicitly enable via
  Database.DMLOptions.DuplicateRuleHeader
- Data Loader: follows API behavior (can be bypassed with header)
- Bulk API: Duplicate Rules are evaluated but can impact performance

To enforce in Apex:
  Database.DMLOptions dmlOpts = new Database.DMLOptions();
  dmlOpts.DuplicateRuleHeader.allowSave = false;
  Database.insert(contact, dmlOpts);
```

**Detection hint:** Flag Duplicate Rule recommendations that claim universal enforcement without noting Apex bypass behavior. Look for missing `DuplicateRuleHeader` in Apex insertion code.

---

## Anti-Pattern 2: Writing Validation Rules That Block Data Migration and Integration Loads

**What the LLM generates:** Validation rules with conditions that always fire regardless of context, such as `AND(ISBLANK(Email), ISBLANK(Phone))` without a bypass condition for system administrators or integration users performing data loads.

**Why it happens:** LLMs generate validation rules for the UI data entry use case without considering that the same rules will block bulk data loads, integrations, and migrations where the incoming data may not have all fields populated.

**Correct pattern:**

```text
Validation rule design for multi-channel orgs:

1. Always include a bypass condition for data loads:
   AND(
     NOT($Permission.Bypass_Validation),
     ISBLANK(Email),
     ISBLANK(Phone)
   )

2. Use Custom Permission "Bypass_Validation" assigned to:
   - Integration user permission sets
   - Data migration permission sets
   - NOT to regular business users

3. Alternative: use a hierarchy Custom Setting:
   AND(
     NOT($Setup.Bypass_Settings__c.Skip_Validation__c),
     your_condition_here
   )

4. Document which validation rules have bypass conditions and which do not.
```

**Detection hint:** Flag validation rules that do not include a bypass condition (`$Permission`, `$Setup`, or `$User` check). Especially flag rules on objects commonly targeted by integrations (Account, Contact, Lead, Opportunity).

---

## Anti-Pattern 3: Recommending Field History Tracking for GDPR Compliance Without Noting Retention Limits

**What the LLM generates:** "Enable Field History Tracking on all PII fields to maintain a GDPR audit trail" without noting that standard Field History Tracking retains data for only 18 months, which may not satisfy compliance requirements.

**Why it happens:** Field History Tracking is free and easy to enable. LLMs recommend it as a compliance solution without distinguishing it from Shield Field Audit Trail (paid, up to 10-year retention).

**Correct pattern:**

```text
Audit trail options for compliance:

Standard Field History Tracking:
- Free with all editions
- 18-month retention (data deleted automatically)
- 20 fields per object maximum
- Sufficient for: operational audit, short-term change tracking

Shield Field Audit Trail:
- Requires Shield license
- Up to 10-year configurable retention
- 60 fields per object
- Data stored in FieldHistoryArchive object
- Required for: FINRA, HIPAA, SOX, long-term GDPR compliance

For GDPR specifically:
- Right to erasure conflicts with audit trail retention
- Document the legal basis for retaining change history
- Field Audit Trail data can be anonymized but not deleted during retention period
```

**Detection hint:** Flag compliance-driven Field History Tracking recommendations that do not mention the 18-month retention limit or evaluate Shield Field Audit Trail.

---

## Anti-Pattern 4: Recommending Hard Delete for GDPR Erasure Without Assessing Cascade Impact

**What the LLM generates:** "To fulfill a GDPR right-to-erasure request, hard-delete the Contact record" without assessing what happens to related records: Cases, Opportunities, Activities, and custom child objects that reference the Contact.

**Why it happens:** GDPR erasure is presented as a straightforward "delete the record" operation. LLMs do not model the cascade effects in Salesforce's relational data model where deleting a Contact can orphan or cascade-delete related records.

**Correct pattern:**

```text
GDPR erasure procedure for Salesforce:

1. Map all relationships from the target record (Contact):
   - Master-detail children: will be CASCADE DELETED
   - Lookup children: lookup field set to null (orphaned)
   - Activities: may be deleted or orphaned depending on configuration

2. Evaluate alternatives to hard delete:
   - Anonymize PII fields (blank Name, hash Email, remove Phone)
   - Retain the record shell for referential integrity
   - This satisfies GDPR erasure while preserving business data relationships

3. If hard delete is required:
   - Export related records first for audit/compliance
   - Delete children before parent to control the sequence
   - Use Bulk API hardDelete to bypass Recycle Bin
   - Document the deletion for compliance records

4. Use Data Mask in sandboxes to prevent PII from propagating to non-production.
```

**Detection hint:** Flag GDPR deletion recommendations that do not assess cascade delete impact on related records. Look for missing relationship analysis before deletion.

---

## Anti-Pattern 5: Treating Data Classification Labels as Access Controls

**What the LLM generates:** "Apply the 'Confidential' data classification label to SSN fields to prevent unauthorized access" — implying that classification labels enforce access restrictions.

**Why it happens:** LLMs conflate data classification (labeling/tagging) with data access control (FLS, sharing, encryption). Salesforce Data Classification is a metadata labeling system — it categorizes fields but does not restrict access.

**Correct pattern:**

```text
Data Classification in Salesforce:

What it does:
- Labels fields with compliance categories (PII, PHI, Confidential, etc.)
- Enables reporting on which fields contain sensitive data
- Helps with GDPR data mapping and compliance audits
- Appears in field metadata but does NOT enforce access restrictions

What it does NOT do:
- Does NOT hide fields from users
- Does NOT encrypt data
- Does NOT replace FLS (Field-Level Security)
- Does NOT trigger alerts on access

To actually protect classified data:
1. FLS: restrict field visibility per profile/permission set
2. Shield Platform Encryption: encrypt at rest
3. Data Mask: protect in non-production environments
4. Transaction Security Policies: alert on sensitive data access patterns
```

**Detection hint:** Flag recommendations that imply data classification labels enforce access control. Look for "classify as Confidential to protect" language without FLS or encryption references.
