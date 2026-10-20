# Platform Encryption — Work Template

Use this template when scoping or executing a Shield Platform Encryption rollout, field-level encryption decision, or key management review.

## Scope

**Skill:** `platform-encryption`

**Request summary:** (fill in what the user asked for — e.g., "Enable Shield encryption on Contact PII fields for HIPAA compliance")

---

## 1. Context Gathered

Answer these before proceeding:

- **Shield license confirmed?** Yes / No / Check with Salesforce AE
- **Target org edition:** (record it; UNVERIFIED (2026-10-20): which editions can buy the Shield / Platform Encryption add-on is Help-only — the corpus names only the add-on subscription, obj 264 L134305)
- **Compliance mandate driving this request:** (HIPAA / PCI-DSS / GDPR / Internal policy / Other)
- **Key management model chosen:** Salesforce-managed / BYOK / Cache-Only Keys
- **Existing data volume on target objects (approximate):** (needed for background-encryption planning)
- **Field history / Field Audit Trail on these fields?** (decides `enableEncryptFieldHistory` and the `FieldHistoryArchive` re-archive question — secguide 262 L4899-4904)

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
- **Background encryption after rotation:** (how completion is confirmed; rotation limit is once per 24 hours in production — obj 264 L283644)
- **Export before destroy?** (an exported key can be re-imported to restore access — obj 264 L283928-283929)
- **External key service details (Cache-Only only):** URL, SLA, monitoring owner

---

## 5. Permission Assignments

Field-level security is the access control you design. List every profile and permission set that
will keep **FLS Read** on each encrypted field, confirm that everyone absent from this table has had
Read removed, and record the sandbox test of who actually sees plaintext (UNVERIFIED (2026-10-20):
whether Shield uses an "encrypted data permission" — secguide 262 L305-306 — is not settled by the corpus):

| Profile / Permission Set | Reason Needs Plaintext Access (FLS Read retained) |
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
- [ ] FLS reviewed on every encrypted field; Read removed from profiles/permission sets that must not see plaintext; plaintext visibility tested per profile in the sandbox
- [ ] Encryption policy enabled in **sandbox** first; validated by logging in as each affected profile
- [ ] Background encryption confirmed complete for all objects with existing data (api_meta 264 L127877-127882)
- [ ] History duplicates (`enableEncryptFieldHistory`) and archived `FieldHistoryArchive` copies decided (secguide 262 L4899-4904)
- [ ] Key rotation schedule documented and calendar reminders set
- [ ] Rollout summary and key management runbook saved to team knowledge base
- [ ] Encryption policy enabled in **production**

---

## 7. Notes and Deviations

Document any deviations from the standard pattern and why:

- (e.g., "No history decision needed for Account.Notes__c because the field is not history-tracked")
- (e.g., "Using BYOK instead of Salesforce-managed keys per security team mandate from audit finding #23")
