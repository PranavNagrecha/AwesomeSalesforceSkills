# Examples — Customer Data Subject Request (DSR) Workflow

## Example 1: GDPR delete for a Lead + converted Contact

**Context:** EU subject asks for erasure; Lead was converted 9 months ago.

**Problem:** Deleting the Contact breaks Case history FKs.

**Solution:**

Run Privacy Center 'Right to Be Forgotten' policy scoped to that subject; it pseudonymizes the Contact (Name='Redacted', Email=null, PII custom fields nulled) while preserving referential integrity. Related Lead is hard-deleted.

**Why it works:** Pseudonymization satisfies GDPR 'erasure' where full deletion would orphan downstream records.


---

## Example 2: Apex batch equivalent for orgs without Privacy Center

**Context:** Platform license, no Privacy Center.

**Problem:** Must delete/pseudonymize 12 objects consistently within 30 days.

**Solution:**

Define a DSR_Policy__mdt with (Object, Field, Action=NULL|REDACT|DELETE). A Queueable walks the policy and runs one SOQL+DML per object for the subject's Ids. An audit object DSR_Action__c captures every row touched with a hash of the original value.

**Why it works:** Policy-as-data lets compliance update scope without Apex redeploy; audit gives legal the record they need.

