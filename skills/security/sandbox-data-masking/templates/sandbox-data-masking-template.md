# Sandbox Data Masking — Work Template

Use this template when planning or reviewing a Data Mask implementation for a sandbox environment.

---

## Scope

**Skill:** `sandbox-data-masking`

**Request summary:** (describe what was asked: new configuration, post-incident review, compliance audit, etc.)

**Sandbox name:** ___________________________

**Sandbox type:** [ ] Partial Copy  [ ] Full Copy  *(Data Mask not available for Developer / Developer Pro)*

**Compliance requirements driving this work:** [ ] GDPR  [ ] HIPAA  [ ] CCPA  [ ] Internal policy

---

## Context Gathered

Answer these before proceeding:

| Question | Answer |
|---|---|
| Is the Data Mask add-on licensed for this org? | |
| Which user/profile will run the masking job? Do they have the Data Mask permission set? | |
| Is Shield Platform Encryption enabled on any fields in scope? (list them) | |
| Are any fields in scope stored in Big Objects or External Objects? | |
| Does the org use SandboxPostCopy automation today? | |

---

## PII / PHI Field Inventory

List every object and field containing regulated data. Complete this before configuring masking.

| Object API Name | Field API Name | Field Type | Required? | Encrypted? | Proposed Masking Type |
|---|---|---|---|---|---|
| Contact | Email | Email | No | No | Pseudonymous |
| Contact | Phone | Phone | No | No | Pseudonymous |
| *(add rows)* | | | | | |

**Masking type key:**
- `Pseudonymous` — replace with realistic fake value (preserves format)
- `Deterministic` — same input always gives same output (use when cross-object FK consistency needed)
- `Null/Delete` — blank the field (only for non-required fields where value is irrelevant to tests)
- `N/A — Encrypted` — field is Shield-encrypted; Data Mask cannot mask it; document as gap
- `N/A — Big Object` — not supported by Data Mask; document as gap

---

## Compliance Gap Register

Document any fields that cannot be masked by Data Mask and the accepted remediation:

| Object | Field | Reason Not Maskable | Remediation / Acceptance |
|---|---|---|---|
| | | | |

---

## Data Mask Configuration Plan

**Configuration name:** ___________________________

| Object | Field | Masking Type | Notes |
|---|---|---|---|
| | | | |

---

## SandboxPostCopy Automation

- [ ] SandboxPostCopy Apex class exists and is version-controlled
- [ ] Class invokes the Data Mask configuration named above
- [ ] Class is registered for the target sandbox in Setup

SandboxPostCopy class name: ___________________________

---

## Post-Masking Verification Queries

Run these after each masking job to confirm effectiveness:

```sql
-- Spot check Contact PII
SELECT Id, Email, Phone FROM Contact LIMIT 5

-- Spot check Lead PII
SELECT Id, Email, Phone FROM Lead LIMIT 5

-- Add object-specific queries for custom PII fields below:

```

Expected result: No value should match a known production email domain or real phone number format.

---

## Review Checklist

- [ ] Data Mask licensed and permission set assigned
- [ ] All PII/PHI fields inventoried and mapped to a masking policy
- [ ] No encrypted fields included in masking policy (would be silently skipped)
- [ ] No required fields configured for Null/Delete masking (would abort the job mid-run)
- [ ] Big Objects and External Objects documented in Compliance Gap Register
- [ ] Masking job completed without errors — checked job log in Data Mask app
- [ ] Spot-check SOQL queries confirm values are masked
- [ ] SandboxPostCopy automation tested on most recent refresh
- [ ] Sandbox access NOT granted until all checklist items above are complete

---

## Notes

*(Record any deviations from standard configuration, decisions made, or follow-up items.)*
