# Examples — Sandbox Data Masking

## Example 1: Masking PII Across Contact and Lead Objects for GDPR Compliance

**Context:** A UK-based Salesforce org stores Contact.Email, Contact.Phone, Contact.MailingStreet, Lead.Email, and Lead.Phone. A QA team needs access to a full copy sandbox to run regression tests. The compliance team has flagged that real customer data must not be visible in non-production environments under GDPR Article 25 (data protection by design and by default).

**Problem:** Without masking, every developer and QA engineer with sandbox access can query real customer email addresses and phone numbers. The sandbox profile grants broad data access for testing purposes, making it impractical to restrict via field-level security alone.

**Solution:**

Configure a Data Mask policy covering all five fields using **Replace from Library** masking, which draws similarly mapped words from a Salesforce-supplied library and so preserves realistic format for email deliverability testing:

1. Open the Data Mask app in the sandbox.
2. Create a new Configuration named "GDPR-QA-Baseline".
3. Add the `Contact` object. Set `Email` to Replace from Library, `Phone` to Replace from Library, `MailingStreet` to Delete/Delete.
4. Add the `Lead` object. Set `Email` to Replace from Library, `Phone` to Replace from Library.
5. Save the configuration.
6. Run the configuration manually for the first cycle. Verify completion in the job log.
7. Wire the configuration to a `SandboxPostCopy` Apex class for future automated runs.

After the job completes, run a spot-check:

```sql
SELECT Email, Phone, MailingStreet FROM Contact LIMIT 5
SELECT Email, Phone FROM Lead LIMIT 5
```

Confirm that Email values end in a Salesforce-generated fake domain (not your production domain), Phone values are replaced with generated numbers, and MailingStreet is blank.

**Why it works:** Replace-from-Library masking substitutes similarly mapped words drawn from a Salesforce-supplied library, so the result is realistic fake data rather than random characters. The format (valid email structure, valid phone format) is preserved so email validation and phone formatting logic in tests still executes correctly. Real customer data is not accessible to sandbox users, satisfying the GDPR requirement.

---

## Example 2: Restoring Cross-Object Value Consistency After Masking in a CPQ Environment

**Context:** An org uses Salesforce CPQ. Quotes reference Contacts, and the Contact email address is also stored on the Quote record as `Quote.BillingContactEmail__c` (a custom field). A data migration test requires the email on the Quote to match the email on the Contact after masking so foreign-key validation logic does not produce false failures.

**Problem:** Data Mask replaces each field independently, so `Contact.Email` and `Quote.BillingContactEmail__c` receive different values and the migration test's join query fails.

**There is no masking type that fixes this.** Data Mask offers exactly four types — Random Characters, Library, Pattern, Delete — and none of them guarantee that the same input yields the same output. That guarantee is deliberately absent: masking is irreversible by design, and a stable input-to-output mapping is exactly what would make it reversible by frequency analysis. Do not go looking for a "Deterministic" or "Consistent" option in the Data Mask UI; it does not exist.

**Solution:** mask both fields, then repair the relationship yourself as a step in the post-refresh runbook.

Configuration steps:
1. In the Data Mask app, open the "CPQ-Migration-Test" configuration.
2. Set `Contact.Email` masking type to **Replace from Library** (keeps a valid email shape).
3. Set `Quote.BillingContactEmail__c` to the same type — its value will differ, and that is expected.
4. Run the configuration.
5. Run a post-mask reconciliation job that copies the now-masked `Contact.Email` onto the related `Quote.BillingContactEmail__c`. A Batch Apex class invoked from the same `SandboxPostCopy` implementation, immediately after the masking job reports complete, is the usual home for this. Treat it as part of the masking deliverable, not as an afterthought — if it is skipped, the join failures look like migration bugs.

Alternatively, drop `Quote.BillingContactEmail__c` from the masking configuration entirely and have the reconciliation job overwrite it from the masked Contact. The denormalised copy then carries no unmasked production data at any point.

Post-run verification query:
```sql
SELECT c.Email, q.BillingContactEmail__c
FROM Contact c
JOIN Quote q ON q.ContactId = c.Id
LIMIT 10
```

Confirm that `c.Email` and `q.BillingContactEmail__c` match for each row.

**Why it works:** The consistency requirement is met by an explicit reconciliation step rather than by a masking property. This is the honest architecture: Data Mask guarantees only that production values are gone and unrecoverable, and any relationship you need preserved across objects is your job to re-establish after the fact.

---

## Anti-Pattern: Relying on Field-Level Security to Protect PII in Sandboxes

**What practitioners do:** Teams restrict PII fields (Contact.Email, Contact.SSN__c) using field-level security on sandbox profiles, assuming developers cannot see the values. They skip Data Mask because "the fields are hidden."

**What goes wrong:** Field-level security controls UI visibility and API access for the running user's profile, and System Administrator profiles — which most developers use in sandboxes — hold field permissions on those PII fields anyway, so FLS restricts nothing for them. Nor does a SOQL query necessarily check FLS at all, and what decides that is the `apiVersion` in the class's `.cls-meta.xml`, not the org's release: at **67.0+ (Summer '26)** SOQL runs in user mode by default and `WITH USER_MODE` states that intent explicitly — `WITH SECURITY_ENFORCED` was removed at 67.0 and no longer compiles (`WITH SECURITY_ENFORCED is no longer supported, use WITH USER_MODE instead`); at **57.0–66.0** the query runs in system mode unless it carries `WITH USER_MODE`; at **≤56.0** `WITH SECURITY_ENFORCED` is the clause available. Anonymous Apex in the Developer Console runs as the developer's own user, which for an admin means every field. Developers can trivially query `SELECT Email FROM Contact` and see real values regardless of profile restrictions.

**Correct approach:** FLS is not a data anonymization control. Data Mask is the correct control for sandbox environments. Apply Data Mask masking policies to all PII fields, and do not grant sandbox access until the masking job has completed successfully.
