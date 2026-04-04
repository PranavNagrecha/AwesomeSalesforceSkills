# Data Quality and Governance — Assessment Template

Use this template when conducting a data quality and governance assessment for a Salesforce org. Fill in each section before implementing changes or presenting findings.

---

## Scope

**Org Name / Sandbox:**
**Assessment Date:**
**Conducted By:**
**Objects in Scope:**
**Compliance Frameworks in Scope (GDPR / HIPAA / CCPA / Internal):**
**Salesforce Edition:**
**Shield Licensed:** Yes / No
**Duplicate Management Licensed:** Yes / No

---

## Section 1: Validation Rules Inventory

For each object in scope, list all active validation rules and their bypass status.

| Object | Rule Name | Description | Has Custom Permission Bypass | Bypass Permission Name | Fires on API Updates | Reviewed |
|---|---|---|---|---|---|---|
| | | | Yes / No | | Yes (all rules do) | |
| | | | Yes / No | | Yes (all rules do) | |
| | | | Yes / No | | Yes (all rules do) | |

**Bypass Summary:**
- Total validation rules reviewed: ___
- Rules with Custom Permission bypass: ___
- Rules using Profile-based bypass (flag for remediation): ___
- Rules with no bypass mechanism (flag for integration risk): ___

**Migration / Integration Readiness:**
- [ ] All rules have a Custom Permission bypass configured
- [ ] Integration user Permission Set includes bypass permission
- [ ] Bypass permission assignment/revocation is documented in runbook

---

## Section 2: Duplicate Rule Coverage Matrix

For each primary object, document the Duplicate Rule and Matching Rule configuration.

| Object | Matching Rule | Match Fields | Match Method (Exact/Fuzzy) | Duplicate Rule Name | Mode (Alert/Block/Report) | Active | Apex DML Bypass Handled | Bulk API 2.0 Bypass Handled |
|---|---|---|---|---|---|---|---|---|
| Account | | | | | | Yes / No | Yes / No | Yes / No |
| Contact | | | | | | Yes / No | Yes / No | Yes / No |
| Lead | | | | | | Yes / No | Yes / No | Yes / No |
| | | | | | | Yes / No | Yes / No | Yes / No |

**Duplicate Rule Assessment:**
- Objects in Block mode: ___
- Objects in Alert-only mode on critical objects (flag for upgrade to Block): ___
- Objects with no Duplicate Rule (flag for gap): ___
- Apex DML operations that set `DMLOptions.DuplicateRuleHeader`: confirmed / not confirmed / not applicable

**Duplicate Backlog:**
- Total records in `DuplicateRecordSet` for Account: ___
- Total records in `DuplicateRecordSet` for Contact: ___
- Third-party dedupe tool engaged for backlog: Yes / No / Not needed

---

## Section 3: Field History Configuration

For each object, document which fields are tracked and retention tier.

| Object | History Object | Fields Tracked (list up to 20) | Field Count | Approaching Limit (>18)? | Retention Tier | Initial Value Gap Addressed |
|---|---|---|---|---|---|---|
| | XxxHistory | | / 20 | Yes / No | Standard 18mo / Shield 10yr | Yes / No |
| | XxxHistory | | / 20 | Yes / No | Standard 18mo / Shield 10yr | Yes / No |
| | XxxHistory | | / 20 | Yes / No | Standard 18mo / Shield 10yr | Yes / No |

**Field History Assessment:**
- Objects with field history enabled: ___
- Objects with zero history-tracked fields that should have history: ___
- Objects at or near 20-field limit: ___
- Shield Field Audit Trail enabled for objects requiring >18 month retention: Yes / No / Not applicable
- Initial value gap mitigated via Apex trigger for compliance-critical fields: Yes / No / Not applicable

**History Query Verification (confirm data is being captured):**
```soql
-- Run for each critical object. A zero-row result on an active object is a red flag.
SELECT Field, OldValue, NewValue, CreatedById, CreatedDate
FROM [ObjectName]History
WHERE CreatedDate = LAST_N_DAYS:30
LIMIT 10
```

---

## Section 4: PII and Data Classification

Inventory of all fields containing or potentially containing PII or sensitive data.

| Object | Field API Name | Field Label | Data Type | Data Sensitivity Level | Compliance Categorization | FLS Restricted | Encrypted (Shield) | Masked in UI | Notes |
|---|---|---|---|---|---|---|---|---|---|
| Contact | FirstName | First Name | Text | Confidential | GDPR | Yes / No | Yes / No | Yes / No | |
| Contact | LastName | Last Name | Text | Confidential | GDPR | Yes / No | Yes / No | Yes / No | |
| Contact | Email | Email | Email | Confidential | GDPR | Yes / No | Yes / No | Yes / No | |
| Contact | Phone | Phone | Phone | Confidential | GDPR | Yes / No | Yes / No | Yes / No | |
| | | | | | | Yes / No | Yes / No | Yes / No | |

**Classification Summary:**
- Total PII fields inventoried: ___
- Fields with `Data Sensitivity Level` set: ___
- Fields with `Compliance Categorization` set: ___
- PII fields with FLS restricted to appropriate profiles/permission sets: ___
- PII fields encrypted with Shield: ___
- PII fields identified by Einstein Data Detect (if Shield licensed): ___
- Unclassified fields suspected to contain PII (flag for remediation): ___

---

## Section 5: GDPR / Compliance Checklist

| Item | Status | Notes |
|---|---|---|
| GDPR erasure runbook documented and tested in sandbox | Done / Pending / N/A | |
| Anonymization token format defined (e.g., ERASED-<RecordId>) | Done / Pending / N/A | |
| `Data_Erasure_Log__c` custom object exists and is populated on each erasure | Done / Pending / N/A | |
| All PII fields included in anonymization script (no omissions) | Done / Pending / N/A | |
| Related record PII (Case Subject, Activity Description) handled | Done / Pending / N/A | |
| Data retention policy defined with cutoff dates per object | Done / Pending / N/A | |
| `Retention_Expires__c` (or equivalent) field exists on retention-governed objects | Done / Pending / N/A | |
| Scheduled batch or Flow enforcing retention cutoffs is active | Done / Pending / N/A | |
| Retention enforcement batch has monitoring / alerting on failure | Done / Pending / N/A | |
| Data classification metadata (`Data Sensitivity Level`) set on all PII fields | Done / Pending / N/A | |
| Right-to-access request process defined (what data we hold, how to extract) | Done / Pending / N/A | |
| Data processing agreements (DPAs) with Salesforce confirmed current | Done / Pending / N/A | |

---

## Section 6: Shield Configuration (If Licensed)

| Item | Status | Notes |
|---|---|---|
| Shield Field Audit Trail enabled on required objects | Done / Pending / N/A | |
| Retention policy set to required duration (up to 10 years) in Field Audit Trail settings | Done / Pending / N/A | |
| `FieldHistoryArchive` queryable for all Shield-tracked objects | Done / Pending / N/A | |
| Shield Platform Encryption enabled on designated PII fields | Done / Pending / N/A | |
| Encrypted fields verified to not be used in: formulas, roll-ups, default values | Done / Pending / N/A | |
| SOQL searches on encrypted fields reviewed (LIKE queries will fail) | Done / Pending / N/A | |
| Encryption key rotation schedule defined | Done / Pending / N/A | |
| BYOK (Bring Your Own Key) configured if required by security policy | Done / Pending / N/A | |
| Einstein Data Detect scan run and findings reviewed | Done / Pending / N/A | |
| Event Monitoring enabled and audit logs retained per policy | Done / Pending / N/A | |

---

## Section 7: Audit Script Results

Run `python3 skills/data/data-quality-and-governance/scripts/check_data_quality.py --manifest-dir <path>` and paste the output below.

```
[paste audit script output here]
```

**Issues Identified by Script:**
- Validation rules without bypass: ___
- Objects with no history-tracked fields: ___
- Duplicate rules in alert-only mode on critical objects: ___

**Remediation Actions Required:**

| Issue | Affected Object/Rule | Owner | Due Date | Status |
|---|---|---|---|---|
| | | | | |
| | | | | |

---

## Section 8: Summary and Recommendations

**Overall Data Quality Posture:** Red / Amber / Green

**Top 3 Priority Findings:**

1.
2.
3.

**Recommended Next Steps:**

1.
2.
3.

**Sign-off:**
- Reviewed by:
- Date:
- Next review due:
