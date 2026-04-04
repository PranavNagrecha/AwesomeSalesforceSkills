# Examples — Sandbox Refresh and Templates

---

## Example 1: Automating Post-Refresh Setup with SandboxPostCopy

**Context:** A mid-size org has a Full sandbox used for UAT. After every refresh, the release manager spends 2–3 hours manually resetting custom settings, aborting scheduled batch jobs, and updating integration endpoints. The process is undocumented and error-prone, and twice in the past year a scheduled job has fired against production data from the sandbox.

**Problem:** There is no SandboxPostCopy class registered on the sandbox. All post-refresh work is manual and depends on whoever initiates the refresh remembering all the steps. Scheduled jobs copied from production run in the sandbox and have caused duplicate records in a connected external system.

**Solution:**

Create a global SandboxPostCopy class in production that handles the repeatable steps:

```apex
global class UAT_SandboxSetup implements SandboxPostCopy {

    global void runApexClass(SandboxContext context) {
        String sandboxName = context.sandboxName();
        String orgId      = context.organizationId();

        // 1. Update org-wide custom settings with new sandbox org ID
        Integration_Config__c cfg = Integration_Config__c.getOrgDefaults();
        cfg.Org_Id__c            = orgId;
        cfg.Environment__c       = sandboxName;
        cfg.Endpoint_Base_URL__c = 'https://sandbox-api.example.com';
        upsert cfg;

        // 2. Abort all scheduled jobs — none should run against production endpoints
        List<CronTrigger> jobs = [
            SELECT Id FROM CronTrigger WHERE State IN ('WAITING', 'ACQUIRED')
        ];
        for (CronTrigger ct : jobs) {
            System.abortJob(ct.Id);
        }

        // 3. Set email deliverability to system-only to prevent outbound test emails
        // (Email deliverability cannot be set via Apex — document this as a manual step)
    }
}
```

Register `UAT_SandboxSetup` in the Apex Class field when initiating the refresh from Setup > Sandboxes.

**Why it works:** The `runApexClass` method is the only Salesforce-supported hook that fires automatically inside the sandbox at the end of copy. By running under the sandbox's own execution context, it can perform DML against sandbox records without affecting production. The `SandboxContext` object provides the new org ID so stored values are always current after refresh.

---

## Example 2: Sandbox Template for a QA Partial Copy Sandbox

**Context:** A QA team uses a Partial Copy sandbox for regression testing. After each refresh the sandbox sometimes contains Accounts and Contacts from unrelated industries, making test scenarios hard to follow. The team has also hit issues where required parent records (PricebookEntry, Product2) were missing because they were not included in the random sample.

**Problem:** No sandbox template was defined. The Partial Copy sandbox selects records at random, producing a data set that does not represent the team's test scenarios and breaks referential integrity for order-related tests.

**Solution:**

Define a sandbox template in Production under Setup > Sandbox Templates before the next refresh:

| Object | Record Count Cap | Notes |
|---|---|---|
| Account | 500 | Core object — parent for most test scenarios |
| Contact | 1000 | Child of Account — referential integrity followed automatically |
| Opportunity | 500 | Sales pipeline tests |
| Product2 | All | Small catalog — take all records to avoid broken PricebookEntry refs |
| Pricebook2 | All | Required for Order/Quote tests |
| PricebookEntry | All | Junction between Pricebook and Product |
| Case | 300 | Service cloud regression scenarios |

Attach this template to the QA sandbox before clicking Refresh.

**Why it works:** The template instructs Salesforce which objects to sample and caps the number of records per object, providing a predictable data set. Including the full Product2, Pricebook2, and PricebookEntry objects removes broken-reference failures on Opportunity and Order tests. Salesforce follows parent lookups automatically, so Contacts will pull their parent Accounts even if the Account count cap would otherwise exclude them.

---

## Example 3: Masking PII in a Partial Copy Sandbox via SandboxPostCopy

**Context:** An org has a Partial Copy sandbox that includes real Contact records with email addresses and phone numbers. Developers work in this sandbox and have inadvertently sent emails to real customers from sandbox workflows.

**Problem:** Sensitive PII is copied from production into the sandbox. No masking runs after refresh, leaving real email addresses active in sandbox records.

**Solution:**

Extend the SandboxPostCopy class to scrub email and phone fields after copy:

```apex
global class QA_SandboxSetup implements SandboxPostCopy {

    global void runApexClass(SandboxContext context) {
        String sandboxName = context.sandboxName();

        // Mask Contact emails and phones — run asynchronously to avoid
        // hitting DML row limits in the synchronous post-copy context
        System.enqueueJob(new MaskContactDataQueueable());
    }
}

public class MaskContactDataQueueable implements Queueable {
    public void execute(QueueableContext ctx) {
        List<Contact> contacts = [
            SELECT Id, Email, Phone FROM Contact WHERE Email != null LIMIT 10000
        ];
        for (Contact c : contacts) {
            if (c.Email != null) {
                c.Email = c.Id + '@example-sandbox.invalid';
            }
            if (c.Phone != null) {
                c.Phone = '555-000-0000';
            }
        }
        update contacts;
    }
}
```

**Why it works:** Using a Queueable from inside `runApexClass` avoids the synchronous row-limit constraints of the post-copy execution context. The masked email domain (`@example-sandbox.invalid`) is an invalid TLD, so even if a workflow fires it will not deliver. This pattern should be applied to all objects containing PII that flows into sandboxes below Full isolation.

---

## Anti-Pattern: Storing Org ID as a Hardcoded String

**What practitioners do:** Hard-code the sandbox org ID in a custom setting, flow variable, or Apex constant so integrations can identify which environment they are running in.

**What goes wrong:** The org ID changes on every sandbox refresh. After refresh, every check against the hardcoded ID fails. Integration routing breaks silently. The issue is non-obvious and typically only surfaces when an integration test fails and someone traces it back to an env-detection mismatch.

**Correct approach:** Use the `SandboxPostCopy` class to read the new org ID from `context.organizationId()` and write it into a custom setting or custom metadata record on every refresh. Consumer code reads the environment from that custom setting rather than from a hardcoded value.
