# Examples — Sandbox Refresh and Templates

---

## Example 1: Automating Post-Refresh Setup with SandboxPostCopy

**Context:** A mid-size org has a Full sandbox used for UAT. After every refresh the release manager spends hours resetting custom settings, re-creating the scheduled jobs UAT depends on, and updating integration endpoints. The steps are undocumented.

**Problem:** No `SandboxPostCopy` class is named on the sandbox, so all post-refresh work depends on memory. The team also believed production's scheduled jobs were copied and would "fire against production"; in fact scheduled jobs aren't copied on refresh, so UAT simply ran without its nightly jobs for a week.

**Solution:**

```apex
global class UAT_SandboxSetup implements SandboxPostCopy {
    global UAT_SandboxSetup() {}   // the copy process uses the no-arg constructor

    global void runApexClass(SandboxContext context) {
        // 1. Environment values for this sandbox
        Integration_Config__c cfg = Integration_Config__c.getOrgDefaults();
        cfg.Environment__c       = context.sandboxName();
        cfg.Endpoint_Base_URL__c = 'https://sandbox-api.example.com';
        upsert cfg;

        // 2. Scheduled jobs are not copied on refresh: schedule what UAT needs
        System.schedule('UAT nightly sync', '0 0 2 * * ?', new NightlySyncSchedulable());
    }
}
```

```apex
@IsTest
private class UAT_SandboxSetup_Test {
    @IsTest
    static void setsEnvironmentAndSchedulesJob() {
        Test.startTest();
        Test.testSandboxPostCopyScript(new UAT_SandboxSetup(), UserInfo.getOrganizationId(),
            UserInfo.getOrganizationId(), 'uat', true);   // true = run as the Automated Process user
        Test.stopTest();
        Assert.areEqual('uat', Integration_Config__c.getOrgDefaults().Environment__c, 'environment set');
        Assert.areEqual(1, [SELECT COUNT() FROM CronTrigger WHERE CronJobDetail.Name = 'UAT nightly sync'], 'job scheduled');
    }
}
```

Name `UAT_SandboxSetup` in the Apex Class field when refreshing from Setup, or as `apexClassName` in the sandbox definition file.

**Why it works:** `runApexClass` runs automatically at the end of the copy, inside the sandbox. The test uses the overload Salesforce recommends, which runs with the Automated Process user's permissions, so an object that user can't access fails in CI instead of during the refresh.

---

## Example 2: Sandbox Template for a QA Partial Copy Sandbox

**Context:** A QA team uses a Partial Copy sandbox for regression testing. Order-related tests fail after refresh because Product2, Pricebook2, and PricebookEntry rows are missing.

**Problem:** The template selected Account, Contact, and Opportunity but not the catalog objects the order tests depend on.

**Solution:** Edit the sandbox template in production so it selects every object the test suites read, then refresh with that template:

| Object | Why it is in the template |
|---|---|
| Account, Contact | Parents for most test scenarios |
| Opportunity | Sales pipeline tests |
| Product2, Pricebook2, PricebookEntry | Order and quote tests need the catalog |
| Case | Service regression scenarios |

Record the template's `1ps` ID in `config/qa-sandbox-def.json` as `templateId`, so every refresh uses it.

**Why it works:** A sandbox template selects which objects to copy into the sandbox; the failure was an object-selection gap, not a data-volume problem. Keeping the template ID in the definition file stops a refresh from running with a different template by accident.

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

**Why it works:** Using a Queueable from inside `runApexClass` moves the volume work into its own asynchronous transaction with its own limits. The masked email domain (`@example-sandbox.invalid`) is an invalid TLD, so even if a workflow fires it will not deliver. This pattern should be applied to all objects containing PII that is copied into Partial Copy and Full sandboxes.

---

## Anti-Pattern: Storing Org ID as a Hardcoded String

**What practitioners do:** Hard-code an org ID in a custom setting, flow variable, or Apex constant so integrations can identify which environment they are running in.

**What goes wrong:** Values stored in production are copied into the sandbox, where they describe the wrong org. Environment checks pass or fail for the wrong reason, and integration routing breaks silently until someone traces it back to an env-detection mismatch.

**Correct approach:** Read the org ID at runtime with `UserInfo.getOrganizationId()`. Where a stored environment marker is genuinely needed, write it in the `SandboxPostCopy` class from `context.organizationId()` and `context.sandboxName()`.
