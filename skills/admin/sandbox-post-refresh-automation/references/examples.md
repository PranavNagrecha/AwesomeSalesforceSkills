# Examples — Sandbox Post-Refresh Automation

## Example 1 — Email firing from a sandbox to real customers

**Context.** Sandbox refreshed Friday. Monday, a developer runs a
test that triggers a workflow email. The email goes to the real
customer in production user.Email — because user.Email wasn't
masked, deliverability wasn't restricted, and the workflow rule
was active.

**Damage.** Customer confused, sales team escalates, legal asks
about the email's content.

**Right answer.** Combine all three mitigations in post-copy:

```apex
global class SandboxPrep implements SandboxPostCopy {
    global void runApexClass(SandboxContext context) {
        maskEmails();
        deactivateExternallyVisibleProcesses();
    }

    private static void maskEmails() {
        List<User> us = new List<User>();
        for (User u : [SELECT Id, Email FROM User WHERE Email != NULL]) {
            u.Email = u.Email.replace('@', '+sandbox@') + '.invalid';
            us.add(u);
        }
        update us;
    }

    private static void deactivateExternallyVisibleProcesses() {
        // Scheduled jobs that send email externally
        for (CronTrigger ct : [SELECT Id, CronJobDetail.Name FROM CronTrigger
                               WHERE CronJobDetail.Name LIKE '%Email%'
                                  OR CronJobDetail.Name LIKE '%Notify%']) {
            try { System.abortJob(ct.Id); } catch (Exception ex) {}
        }
    }
}
```

PLUS: org-wide deliverability set to "System emails only" as a
backup. Belt-and-suspenders.

---

## Example 2 — Idempotent re-runnability

**Context.** Post-copy class fails halfway through (a query times
out). Half the users have masked emails; half don't. Admin needs
to re-run.

**Wrong code.**

```apex
private static void maskEmails() {
    for (User u : [SELECT Id, Email FROM User]) {
        u.Email = u.Email.replace('@', '+sandbox@') + '.invalid';
        update u;  // single-record DML
    }
}
```

**Why it's wrong.** Re-running re-applies the mask, producing
`alice+sandbox+sandbox@example.com.invalid.invalid`.

**Right code.**

```apex
private static void maskEmails() {
    List<User> us = new List<User>();
    for (User u : [SELECT Id, Email FROM User WHERE Email NOT LIKE '%.invalid' AND Email != NULL]) {
        u.Email = u.Email.replace('@', '+sandbox@') + '.invalid';
        us.add(u);
    }
    if (!us.isEmpty()) update us;
}
```

The `WHERE Email NOT LIKE '%.invalid'` predicate makes re-runs
no-op for already-masked records. Idempotent.

---

## Example 3 — Per-environment branch via `SandboxContext`

**Context.** Different sandbox tiers need different prep. Full
sandbox keeps user accounts; dev sandbox should deactivate everyone
except a small allow-list.

```apex
global void runApexClass(SandboxContext context) {
    String name = context.sandboxName();
    if (name == 'Dev') {
        deactivateAllExceptAllowList();
    } else if (name == 'Full') {
        keepUsersActive();
    }
    // Common steps for all tiers:
    maskEmails();
    scrubIntegrationEndpoints();
}
```

`SandboxContext.sandboxName()` is the human-readable name — what
the admin typed when creating the sandbox. Document the names
your post-copy class branches on.

---

## Example 4 — Scrubbing Custom Setting values

**Context.** `Integration_Config__c` Custom Setting holds prod
endpoint URLs. Post-copy must rewrite to sandbox values.

```apex
private static void scrubIntegrationEndpoints() {
    Integration_Config__c cfg = Integration_Config__c.getOrgDefaults();
    if (cfg == null || cfg.Id == null) {
        cfg = new Integration_Config__c();
    }
    cfg.Endpoint__c = 'https://mock.acme-sandbox.local/api';
    cfg.API_Key__c = 'SANDBOX-MOCK-KEY';
    cfg.Active__c = false;  // disable inbound integrations until reactivated
    upsert cfg;
}
```

For Named Credentials whose URL isn't Apex-mutable, pre-deploy
sandbox-pointing NC metadata as a separate metadata deploy step
that runs after the sandbox is unlocked.

---

## Example 5 — Test class for the post-copy

**Context.** How to test a `SandboxPostCopy` class without actually
refreshing a sandbox.

```apex
@IsTest
private class SandboxPrepTest {
    @IsTest
    static void maskEmailsMasksAll() {
        // Arrange — create a test user with a real-looking email.
        User u = new User(
            Email = 'test@example.com',
            Username = 'sandbox-prep-test@example.com.test',
            FirstName = 'Test', LastName = 'User',
            Alias = 'spt',
            TimeZoneSidKey = 'America/Los_Angeles',
            LocaleSidKey = 'en_US', EmailEncodingKey = 'UTF-8',
            ProfileId = [SELECT Id FROM Profile WHERE Name = 'System Administrator' LIMIT 1].Id,
            LanguageLocaleKey = 'en_US'
        );
        insert u;

        // Act — invoke runApexClass directly (passing a mock SandboxContext).
        Test.startTest();
        Test.testSandboxPostCopyScript(
            new SandboxPrep(),
            UserInfo.getOrganizationId(),
            'Test',
            'TestSandbox'
        );
        Test.stopTest();

        // Assert
        u = [SELECT Email FROM User WHERE Id = :u.Id];
        System.assert(u.Email.endsWith('.invalid'), 'Email should be masked');
    }
}
```

`Test.testSandboxPostCopyScript` is the platform's test harness —
fakes the SandboxContext + runApexClass invocation.

---

## Anti-Pattern: Post-copy class that does deletes without idempotency

```apex
delete [SELECT Id FROM Account WHERE Test_Data__c = TRUE];
delete [SELECT Id FROM Contact WHERE Test_Data__c = TRUE];
```

**What goes wrong.** First refresh: clears existing test data
(intended). Subsequent refresh: there ARE no test-data records yet
because they're created later in the post-copy. Delete is no-op
(fine). But if a developer adds Test_Data__c = TRUE to a record
before refresh, refresh deletes it.

**Correct.** Scope the delete to records OLDER than the refresh
date, or scope to a "post-copy-managed" tag rather than the broader
test-data tag. Idempotency includes "won't delete things created
intentionally between refreshes".
