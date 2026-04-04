# Platform Encryption — Work Template

Use this template when scoping or executing a Shield Platform Encryption rollout, field-level encryption decision, or key management review.

## Scope

**Skill:** `platform-encryption`

**Request summary:** (fill in what the user asked for — e.g., "Enable Shield encryption on Contact PII fields for HIPAA compliance")

---

## 1. Context Gathered

Answer these before proceeding:

- **Shield license confirmed?** Yes / No / Check with Salesforce AE
- **Target org edition:** Enterprise / Performance / Unlimited / Developer
- **Compliance mandate driving this request:** (HIPAA / PCI-DSS / GDPR / Internal policy / Other)
- **Key management model chosen:** Salesforce-managed / BYOK / Cache-Only Keys
- **Existing data volume on target objects (approximate):** (needed for re-encryption job planning)

---

## 2. Field Encryption Matrix

For each field requiring encryption, complete this table before enabling any policy:

| Object | Field API Name | Field Type | Used in SOQL Filter? | Used in Report/List View Filter? | Used in Flow/Automation Criteria? | Used in Sharing Rule? | Recommended Scheme | Notes |
|---|---|---|---|---|---|---|---|---|
| Contact | SSN__c | Text | No | No | No | No | Probabilistic | Display-only |
| Contact | Email | Email | Yes (dedup query) | Yes | Yes (matching) | No | Deterministic | Equality filters only after encryption |
| Account | BankAccountNumber__c | Text | No | No | No | No | Probabilistic | Display-only |
| (add rows as needed) | | | | | | | | |

---

## 3. SOQL Impact Assessment

List every SOQL query, Flow element, report filter, or list view that uses the fields in the matrix above as a filter criterion:

| Location | Field Referenced | Current Filter Operator | Action Required |
|---|---|---|---|
| AccountService.cls line 42 | Email | = (equality) | No change needed if deterministic |
| LeadMatchingFlow | Email | contains | Change to exact match or redesign |
| Contacts List View | SSN__c | contains | Remove filter; SSN is display-only |
| (add rows as needed) | | | |

---

## 4. Key Management Decision

- **Chosen model:** (Salesforce-managed / BYOK / Cache-Only)
- **Justification:** (reference the compliance mandate or security requirement)
- **Key rotation frequency:** (e.g., quarterly, annually)
- **Owner of key rotation:** (team name or role)
- **Re-encryption cadence after rotation:** (immediately, scheduled, never)
- **External key service details (Cache-Only only):** URL, SLA, monitoring owner

---

## 5. Permission Assignments

List all profiles and permission sets that need the View Encrypted Data permission:

| Profile / Permission Set | Reason Needs Plaintext Access |
|---|---|
| System Administrator | Full admin access |
| Integration User — MuleSoft | Record matching by Email |
| Service Agent — Standard | Viewing Contact details |
| (add rows as needed) | |

---

## 6. Rollout Checklist

Copy this checklist and tick items as you complete them:

- [ ] Shield Platform Encryption license confirmed as active in target org
- [ ] Field encryption matrix completed and reviewed by security team
- [ ] SOQL impact assessment completed; all affected queries identified
- [ ] Reports and list views using affected fields as filter criteria updated or removed
- [ ] Flows and automations referencing affected fields audited
- [ ] Sharing rules referencing affected fields reviewed (encryption breaks criteria-based sharing)
- [ ] Key management model selected; tenant secret generated or customer key material uploaded
- [ ] View Encrypted Data permission assigned to all required profiles and permission sets
- [ ] Encryption policy enabled in **sandbox** first; validated by logging in as each affected profile
- [ ] Re-encryption job initiated and completed for all objects with existing data
- [ ] Encryption Statistics page reviewed to confirm encrypted record counts are correct
- [ ] Key rotation schedule documented and calendar reminders set
- [ ] Rollout summary and key management runbook saved to team knowledge base
- [ ] Encryption policy enabled in **production**

---

## 7. Notes and Deviations

Document any deviations from the standard pattern and why:

- (e.g., "Skipped re-encryption for Account.Notes__c because field was always blank before encryption was enabled")
- (e.g., "Using BYOK instead of Salesforce-managed keys per security team mandate from audit finding #23")
