# Examples — Sandbox Data Masking

## Example 1: Masking PII Across Contact and Lead Objects for GDPR Compliance

**Context:** A UK-based Salesforce org stores Contact.Email, Contact.Phone, Contact.MailingStreet, Lead.Email, and Lead.Phone. A QA team needs access to a full copy sandbox to run regression tests. The compliance team has flagged that real customer data must not be visible in non-production environments under GDPR Article 25 (data protection by design and by default).

**Problem:** Without masking, every developer and QA engineer with sandbox access can query real customer email addresses and phone numbers. The sandbox profile grants broad data access for testing purposes, making it impractical to restrict via field-level security alone.

**Solution:**

Configure a Data Mask policy covering all five fields with pseudonymous masking to preserve realistic format for email deliverability testing:

1. Open the Data Mask app in the sandbox.
2. Create a new Configuration named "GDPR-QA-Baseline".
3. Add the `Contact` object. Set `Email` to Pseudonymous, `Phone` to Pseudonymous, `MailingStreet` to Null/Delete.
4. Add the `Lead` object. Set `Email` to Pseudonymous, `Phone` to Pseudonymous.
5. Save the configuration.
6. Run the configuration manually for the first cycle. Verify completion in the job log.
7. Wire the configuration to a `SandboxPostCopy` Apex class for future automated runs.

After the job completes, run a spot-check:

```sql
SELECT Email, Phone, MailingStreet FROM Contact LIMIT 5
SELECT Email, Phone FROM Lead LIMIT 5
```

Confirm that Email values end in a Salesforce-generated fake domain (not your production domain), Phone values are replaced with generated numbers, and MailingStreet is blank.

**Why it works:** Pseudonymous masking replaces values with realistic fake data from Salesforce's internal library. The format (valid email structure, valid phone format) is preserved so email validation and phone formatting logic in tests still executes correctly. Real customer data is not accessible to sandbox users, satisfying the GDPR requirement.

---

## Example 2: Deterministic Masking for Cross-Object Consistency in a CPQ Environment

**Context:** An org uses Salesforce CPQ. Quotes reference Contacts, and the Contact email address is also stored on the Quote record as `Quote.BillingContactEmail__c` (a custom field). A data migration test requires the email on the Quote to match the email on the Contact after masking so foreign-key validation logic does not produce false failures.

**Problem:** If pseudonymous masking is applied independently to `Contact.Email` and `Quote.BillingContactEmail__c`, each field receives a different randomly generated value. The migration test's join query fails because the two fields no longer match. This looks like a data integrity bug but is actually a masking configuration issue.

**Solution:**

Use deterministic masking on both fields within the same Data Mask configuration. Deterministic masking ensures that the same input value always produces the same output value within a single masking run.

Configuration steps:
1. In the Data Mask app, open the "CPQ-Migration-Test" configuration.
2. Set `Contact.Email` masking type to **Deterministic**.
3. Set `Quote.BillingContactEmail__c` masking type to **Deterministic**.
4. Run the configuration.

Post-run verification query:
```sql
SELECT c.Email, q.BillingContactEmail__c
FROM Contact c
JOIN Quote q ON q.ContactId = c.Id
LIMIT 10
```

Confirm that `c.Email` and `q.BillingContactEmail__c` match for each row.

**Why it works:** Deterministic masking applies a consistent transformation function. Given the same input "jane@realcompany.com", the same output "xkq7@datamask.example.com" is produced wherever that value appears in the run — across both the Contact and the Quote — preserving the cross-object relationship needed for join-based tests.

---

## Anti-Pattern: Relying on Field-Level Security to Protect PII in Sandboxes

**What practitioners do:** Teams restrict PII fields (Contact.Email, Contact.SSN__c) using field-level security on sandbox profiles, assuming developers cannot see the values. They skip Data Mask because "the fields are hidden."

**What goes wrong:** Field-level security controls UI visibility and API access for the running user's profile, but System Administrator profiles — which most developers use in sandboxes — typically have "View All Data" and can bypass FLS in SOQL with `WITH SECURITY_ENFORCED` disabled. Anonymous Apex execution in the Developer Console bypasses FLS entirely. Developers can trivially query `SELECT Email FROM Contact` and see real values regardless of profile restrictions.

**Correct approach:** FLS is not a data anonymization control. Data Mask is the correct control for sandbox environments. Apply Data Mask masking policies to all PII fields, and do not grant sandbox access until the masking job has completed successfully.
