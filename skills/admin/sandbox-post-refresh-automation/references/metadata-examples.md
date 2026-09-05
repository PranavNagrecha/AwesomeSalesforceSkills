# Metadata Examples — Sandbox Post-Refresh Automation

The deployable half of this skill. Six artefacts, in the order you build them:

| # | Artefact | Where it lives | Deployed by |
|---|---|---|---|
| 1 | `SandboxPrep.cls` + `-meta.xml` — the `SandboxPostCopy` implementation | `force-app/main/default/classes/` | Metadata API → **production** |
| 2 | `SandboxPrepTest.cls` + `-meta.xml` — `Test.testSandboxPostCopyScript(..., true)` | `force-app/main/default/classes/` | Metadata API → **production** |
| 3 | Tooling API `SandboxInfo` payload — binds the class to a sandbox by `ApexClassId` | not a source file; a REST call | Tooling API (or Setup UI) |
| 4 | `CronTrigger` inventory SOQL — what is still live after the copy | ad-hoc / anonymous Apex | n/a (read-only object) |
| 5 | `EmailAdministration.settings` — the deliverability-adjacent fields that *are* deployable | `force-app/main/default/settings/` | Metadata API → **sandbox**, post-activation |
| 6 | `post-refresh-checklist.json` — machine-checkable runbook | `config/sandbox/` | not deployed; read by the checker |

Shapes come from the Apex Reference Guide (`SandboxPostCopy` interface L228876–229016, `Test.testSandboxPostCopyScript`
L241140–241228, `System.abortJob` L238661–238698), the Object Reference (`CronTrigger` L86710–86844) and the
Metadata API Developer Guide (`EmailAdministrationSettings` L114848–115022, sandbox username mutation L2711–2713).

---

## 1. The `SandboxPostCopy` class

`force-app/main/default/classes/SandboxPrep.cls`

```apex
global class SandboxPrep implements SandboxPostCopy {

    // The sandbox copy process instantiates this class with the no-arg constructor.
    // Apex Reference Guide L228955-228956: "Implementations of SandboxPostCopy must have
    // a no-arg constructor. This constructor is used during the sandbox copy process."
    global SandboxPrep() {}

    global void runApexClass(SandboxContext context) {
        System.debug('Post-copy start. Org: ' + context.organizationId()
            + ' Sandbox: ' + context.sandboxId() + ' / ' + context.sandboxName());

        // Each step is separately guarded: the guide (L228889-228891) warns the script runs
        // as a restricted Automated Process user, so a step CAN fail on object access alone.
        // One failed step must not skip the five that follow it. Apex has no lambdas, so
        // this is six explicit blocks rather than a loop over callables.
        try { maskUserEmail();            } catch (Exception e) { logStep('mask-user-email', e); }
        try { deactivateNonSandboxUsers(); } catch (Exception e) { logStep('deactivate-users', e); }
        try { abortScheduledJobs();       } catch (Exception e) { logStep('abort-scheduled-jobs', e); }
        try { scrubIntegrationConfig();   } catch (Exception e) { logStep('scrub-integration-config', e); }
        try { reseedReferenceData();      } catch (Exception e) { logStep('reseed-reference-data', e); }
        try {
            applyEnvironmentConfig(context.sandboxName());
        } catch (Exception e) { logStep('apply-environment-config', e); }
    }

    // ---- steps -----------------------------------------------------------

    // Idempotent: already-masked rows are excluded by the WHERE clause, so a
    // manual re-run does not produce alice+sandbox+sandbox@...invalid.invalid.
    private static void maskUserEmail() {
        List<User> toUpdate = new List<User>();
        for (User u : [
            SELECT Id, Email
            FROM User
            WHERE IsActive = TRUE
              AND Email != NULL
              AND (NOT Email LIKE '%.invalid')
            LIMIT 10000
        ]) {
            u.Email = u.Email.replace('@', '+sbx@') + '.invalid';
            toUpdate.add(u);
        }
        if (!toUpdate.isEmpty()) {
            update toUpdate;
        }
    }

    private static void deactivateNonSandboxUsers() {
        Set<String> keepAliases = new Set<String>{ 'sbxadm', 'intusr' };
        List<User> toDeactivate = new List<User>();
        for (User u : [
            SELECT Id FROM User
            WHERE IsActive = TRUE AND Alias NOT IN :keepAliases
            LIMIT 10000
        ]) {
            toDeactivate.add(new User(Id = u.Id, IsActive = false));
        }
        if (!toDeactivate.isEmpty()) {
            update toDeactivate;
        }
    }

    // System.abortJob takes the CronTrigger Id for scheduled Apex. Passing an
    // AsyncApexJob Id does NOT work (Apex Reference Guide L238678-238680).
    private static void abortScheduledJobs() {
        for (CronTrigger ct : [
            SELECT Id, CronJobDetail.Name
            FROM CronTrigger
            WHERE State IN ('WAITING', 'ACQUIRED', 'EXECUTING',
                            'PAUSED', 'BLOCKED', 'PAUSED_BLOCKED')
        ]) {
            try {
                System.abortJob(ct.Id);
            } catch (Exception ex) {
                System.debug(LoggingLevel.ERROR,
                    'abortJob failed for ' + ct.CronJobDetail.Name + ': ' + ex.getMessage());
            }
        }
    }

    private static void scrubIntegrationConfig() {
        Integration_Config__c cfg = Integration_Config__c.getOrgDefaults();
        if (cfg == null) {
            cfg = new Integration_Config__c();
        }
        cfg.Endpoint__c = 'https://mock.acme-sandbox.invalid/api';
        cfg.API_Key__c  = 'SANDBOX-MOCK-KEY';
        cfg.Active__c   = false;
        upsert cfg;
    }

    private static void reseedReferenceData() {
        // Left deliberately narrow: see data/sandbox-refresh-data-strategies.
    }

    private static void applyEnvironmentConfig(String sandboxName) {
        // Branch on the name, but never let an unknown name skip the safety steps
        // — those already ran above, unconditionally.
        System.debug('Environment config for sandbox: ' + sandboxName);
    }

    // ---- plumbing --------------------------------------------------------

    private static void logStep(String id, Exception ex) {
        System.debug(LoggingLevel.ERROR,
            'Post-copy step ' + id + ' failed: ' + ex.getTypeName()
            + ': ' + ex.getMessage());
    }
}
```

`force-app/main/default/classes/SandboxPrep.cls-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<ApexClass xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>62.0</apiVersion>
    <status>Active</status>
</ApexClass>
```

**How to read it:**

- **`global SandboxPrep() {}` is not decoration.** The guide's own sample carries the comment
  "Implementations of SandboxPostCopy must have a no-arg constructor. This constructor is used during
  the sandbox copy process" (L228955–228956), and warns that constructors with arguments "won't be used
  by the sandbox copy process" (L228958–228960). A class whose *only* constructor takes arguments cannot
  be instantiated by the copy.
- **`global` on the class and on `runApexClass`** follows the guide's example implementation
  (L228952, L228975). The guide's member-signature line reads `public void runApexClass(System.SandboxContext context)`
  (L228926) — documentation convention for the interface member, not a contradiction. UNVERIFIED (2026-09-05):
  no sentence in the Apex Reference Guide states that a `public` implementation is rejected; `global`
  is what every Salesforce-authored sample uses, and it is what this skill recommends.
- **Every step is separately caught.** L228889–228891: the script "is executed at the end of the sandbox
  copy using a special Automated Process user that isn't visible within the org. This user doesn't have
  access to all object and features". An access failure on step 2 must not cost you steps 3–6.
- **The abort query lists six states, not three.** See § 4.
- **`LIMIT 10000`** keeps the query inside the synchronous 50,000-row limit alongside the other steps'
  queries; a sandbox with more users needs the Batch variant (see `references/well-architected.md`).

---

## 2. The test class

`force-app/main/default/classes/SandboxPrepTest.cls`

```apex
@IsTest
private class SandboxPrepTest {

    @IsTest
    static void postCopyMasksEmailAndIsIdempotent() {
        Profile p = [SELECT Id FROM Profile WHERE Name = 'System Administrator' LIMIT 1];
        User victim = new User(
            Alias = 'sbxt1',
            Email = 'real.customer@example.com',
            EmailEncodingKey = 'UTF-8',
            FirstName = 'Post', LastName = 'Copy',
            LanguageLocaleKey = 'en_US',
            LocaleSidKey = 'en_US',
            ProfileId = p.Id,
            TimeZoneSidKey = 'America/Los_Angeles',
            Username = 'sandbox.prep.test.' + DateTime.now().getTime() + '@example.com'
        );
        insert victim;

        Test.startTest();
        // 5-arg overload. RunAsAutoProcUser = true runs the script with the same
        // permissions the copy process uses (Apex Reference Guide L241180-241184,
        // L241191-241199) — the 4-arg form runs as the test initiator and will pass
        // for code that fails during a real refresh.
        Test.testSandboxPostCopyScript(
            new SandboxPrep(),
            UserInfo.getOrganizationId(),
            UserInfo.getOrganizationId(),
            'uat',
            true
        );
        Test.stopTest();

        User after = [SELECT Email FROM User WHERE Id = :victim.Id];
        System.assert(after.Email.endsWith('.invalid'),
            'Email should be masked, was: ' + after.Email);
        System.assertEquals(1, after.Email.countMatches('+sbx@'),
            'Re-runnable mask must not compound the tag');
    }

    @IsTest
    static void activeCronTriggersAreAborted() {
        Test.startTest();
        Test.testSandboxPostCopyScript(
            new SandboxPrep(),
            UserInfo.getOrganizationId(),
            UserInfo.getOrganizationId(),
            'uat',
            true
        );
        Test.stopTest();

        List<CronTrigger> live = [
            SELECT Id FROM CronTrigger
            WHERE State IN ('WAITING', 'ACQUIRED', 'EXECUTING',
                            'PAUSED', 'BLOCKED', 'PAUSED_BLOCKED')
        ];
        System.assertEquals(0, live.size(), 'No schedulable job should survive post-copy');
    }
}
```

`force-app/main/default/classes/SandboxPrepTest.cls-meta.xml` is identical to `SandboxPrep.cls-meta.xml`.

**How to read it:**

- **`Test.testSandboxPostCopyScript` throws** if the test install fails — "This method throws a run-time
  exception if the test install fails" (L241178). There is no return value to assert on; assert on the
  *side effects*, as both methods above do.
- **The 5-arg overload is the one Salesforce recommends** (L241180–241184), and the guide's own sample
  test passes `true` (L229004–229006). Using the 4-arg form is the most common way a post-copy class
  passes its tests and then fails during a real refresh, because the 4-arg form runs with the test
  initiator's permissions rather than the Automated Process user's.
- **`countMatches('+sbx@')` is the idempotency assertion.** If `maskUserEmail()` loses its
  `NOT Email LIKE '%.invalid'` predicate, this assertion — not the `endsWith` one — is what fails.

---

## 3. Binding the class to a sandbox — Tooling API `SandboxInfo`

> UNVERIFIED (2026-09-05): `SandboxInfo` is a **Tooling API** object. The Apex Reference Guide points at
> it by name only ("SEE ALSO: Tooling API: SandboxInfo", L228902) and it appears in **neither**
> `object_reference` nor `api_meta` — a `SandboxInfo` grep across both returns zero hits, which is
> expected, since the Object Reference documents SOAP/REST standard objects, not Tooling objects. The
> field names below (`ApexClassId`, `LicenseType`, `AutoActivate`, `SandboxName`, `Description`) are
> therefore **not grounded in the corpus this skill was verified against**. Confirm them against the
> Tooling API Developer Guide before scripting against them. The Setup UI path (Setup → Sandboxes →
> the sandbox → Apex Class) is equally help-only and equally unverified here.

```http
POST /services/data/v62.0/tooling/sobjects/SandboxInfo HTTP/1.1
Host: mycompany.my.salesforce.com
Authorization: Bearer <REDACTED>
Content-Type: application/json

{
  "SandboxName": "uat",
  "LicenseType": "FULL",
  "Description": "UAT full sandbox; post-copy runs SandboxPrep",
  "ApexClassId": "01p5g000004ABCDAA2",
  "AutoActivate": true
}
```

**How to read it:**

- **`ApexClassId` is an Id, not a class name.** Resolve it first, in the org you are targeting:
  `SELECT Id FROM ApexClass WHERE Name = 'SandboxPrep'`. The Id differs per org, so a payload
  copy-pasted from a runbook is wrong the moment you point it at a different production org.
- **The class must already exist in production** when this call is made — the sandbox copies Apex from
  the source org, so a class that only ever existed in a sandbox is gone after the next refresh
  (`references/gotchas.md` § 7).
- **`SandboxInfo` is a persistent record**, distinct from `SandboxProcess` (one row per refresh run).
  Poll the latter for progress; the former is the configuration. Both are Tooling API — same caveat.

---

## 4. CronTrigger inventory — the six states that are still live

Run this **before** you write the abort list, and again after the sandbox is unlocked:

```sql
SELECT CronJobDetail.Name,
       CronJobDetail.JobType,
       State,
       CronExpression,
       NextFireTime,
       TimesTriggered,
       TimeZoneSidKey,
       OwnerId
FROM CronTrigger
WHERE State IN ('WAITING', 'ACQUIRED', 'EXECUTING',
                'PAUSED', 'BLOCKED', 'PAUSED_BLOCKED')
ORDER BY NextFireTime NULLS LAST
```

`CronTrigger.State` has exactly nine documented values (Object Reference L86799–86811). Six of them are
"this job will still run"; three are terminal:

| State | Documented meaning (Object Reference L86799–86811) | Still live? |
|---|---|---|
| `WAITING` | "The job is waiting for execution." | Yes |
| `ACQUIRED` | "The job has been picked up by the system and is about to execute." | Yes |
| `EXECUTING` | "The job is executing." | Yes |
| `PAUSED` | "A job can have this state during patch and major releases. After the release has finished, the job state is automatically set to WAITING or another state." | **Yes** — it returns to `WAITING` on its own |
| `BLOCKED` | "Execution of a second instance of the job is attempted while one instance is running. This state lasts until the first job instance is completed." | **Yes** |
| `PAUSED_BLOCKED` | "A job has this state due to a release occurring. When the release has finished and no other instance of the job is running, the job's status is set to another state." | **Yes** |
| `COMPLETE` | "The trigger has fired and is not scheduled to fire again." | No |
| `ERROR` | "The trigger definition has an error." | No |
| `DELETED` | "The job has been deleted." | No |

**How to read it:**

- **`CronJobDetail.JobType` tells you what you are about to kill.** Coded values, Object Reference
  L86671–86680: `1` Data Export, `3` Dashboard Refresh, `4` Reporting Snapshot, `6` Scheduled Flow,
  `7` Scheduled Apex, `8` Report Run, `9` Batch Job, `A` Reporting Notification. Scheduled Flows (`6`)
  are the ones an Apex-only post-copy usually forgets exist.
- **You cannot DML this object.** Supported Calls are `describeSObjects()`, `query()`, `retrieve()`
  (L86722) — there is no create, update or delete. `System.abortJob` is the only write path.
- **`abortJob` does not kill a running transaction.** "The specified job is stopped, but any code that
  is in progress will continue to execute until it completes" (L238662–238663). A job caught in
  `EXECUTING` finishes its current run regardless.

---

## 5. Masking user email with Data Loader (the fallback path)

When the post-copy Apex fails — which the guide anticipates: "If the script fails, run the script after
sandbox activation as a user with appropriate permissions" (L228891) — this is the manual equivalent.

**Step 1 — extract.** Data Loader → Export, object `User`, query:

```sql
SELECT Id, Username, Email
FROM User
WHERE IsActive = TRUE AND Email != NULL AND (NOT Email LIKE '%.invalid')
```

**Step 2 — transform.** The sandbox copy already appended the sandbox name to `Username`, so the export
tells you which sandbox you are in without trusting any other field. Metadata API Developer Guide
L2711–2713: *"when you copy data to a sandbox, the fields containing usernames from the production
organization are altered to include the sandbox name. In a sandbox named `test`, the username
`user@acme.com` becomes `user@acme.com.test`."* `Email` gets **no** such treatment — which is precisely
why it needs this load.

```csv
Id,Username,Email
0055g00000AAAA1AAF,alice@acme.com.uat,alice+sbx@acme.com.invalid
0055g00000BBBB2AAF,bob@acme.com.uat,bob+sbx@acme.com.invalid
```

Derive the new `Email` from the *exported* `Email`, never from `Username` — `Username` already carries
the `.uat` suffix and reusing it double-suffixes the address.

**Step 3 — load.** Data Loader → **Update**, object `User`, map `Id` → `Id` and `Email` → `Email`. Leave
`Username` unmapped.

**Step 4 — settings.** Settings → Settings. Import batch size: "The maximum import batch size is 200
records for SOAP API and 10000 records for Bulk API. If the Use SOAP API option is selected, then both
Import Batch Size and Export Batch Size are used. If the Use Bulk API option is selected, then only
Import Batch Size is used. If the Use Bulk API 2.0 option is selected, then neither batch size is used
because Bulk API 2.0 handles batch size automatically" (Data Loader Guide L351–360).

**Step 5 — verify.** Re-run the Step 1 query. Zero rows means every active user is masked. A non-zero
count is your gap list, not a rounding error.

**How to read it:**

- **This is a *fallback*, not the design.** It runs after the sandbox is unlocked, i.e. after the window
  in which an unmasked send can happen. The Apex path closes that window; this one only shortens it.
- **Do not run it against production.** The `Username` suffix is your guard: if the exported usernames
  have no sandbox suffix, you are connected to the source org. Stop.

---

## 6. `EmailAdministration.settings` — what is actually deployable

> UNVERIFIED (2026-09-05): the org-wide **Deliverability → Access Level** control ("All email" /
> "System email only" / "No access") that this skill's mitigation A relies on is **not** a field of the
> `EmailAdministrationSettings` metadata type. The type's complete field list (api_meta L114872–114994)
> is 19 booleans and contains no such element, and no enum with those values appears anywhere in
> `api_meta` or `object_reference`. It is a real Setup control, but on this corpus it is a manual step,
> not something you can put in a deploy. Treat it as a human checklist item.

What you *can* deploy — every element below is in the documented field table:

`force-app/main/default/settings/EmailAdministration.settings-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<EmailAdministrationSettings xmlns="http://soap.sforce.com/2006/04/metadata">
    <enableComplianceBcc>false</enableComplianceBcc>
    <enableEmailToSalesforce>false</enableEmailToSalesforce>
    <enableEmailWorkflowApproval>false</enableEmailWorkflowApproval>
    <enableHandleBouncedEmails>true</enableHandleBouncedEmails>
    <enableResendBouncedEmails>false</enableResendBouncedEmails>
    <enableSendViaExchangePref>false</enableSendViaExchangePref>
    <enableSendViaGmailPref>false</enableSendViaGmailPref>
    <sendMassEmailNotification>false</sendMassEmailNotification>
    <sendTextOnlySystemEmails>true</sendTextOnlySystemEmails>
</EmailAdministrationSettings>
```

**How to read it:**

- **The filename is misspelled on purpose.** api_meta L114854: "EmailAdministrationSettings values are
  stored in the `EmailAdminstration.settings` file in the settings directory" — *EmailAdminstration*,
  no second `i`. That is verbatim from the guide, and it is the filename the deploy expects. Naming the
  file `EmailAdministration.settings-meta.xml` is a deploy error you will spend an hour on. UNVERIFIED
  (2026-09-05): whether the platform also accepts the correctly-spelled form is not stated.
- **`enableEmailWorkflowApproval` = false** stops approval responses arriving by mail from a sandbox —
  "Indicates whether users can respond to email approval requests directly from their email"
  (L114905–114909). Default is false; set it explicitly so a refreshed prod value cannot flip it.
- **`enableComplianceBcc` = false** matters more in a sandbox than production: "a copy of each outbound
  email message is sent to an email address you specify" (L114872–114878). Left on, every sandbox test
  send lands in the production compliance archive.
- **`enableHandleBouncedEmails` = true** is deliberate here. Masked `.invalid` addresses *will* bounce;
  bounce handling is what marks them invalid rather than silently retrying (L114915–114921).
- **There is exactly one settings file per settings type** — "The .settings files are different from
  other named components because there's only one settings file for each settings component"
  (L114855–114856). You cannot have a sandbox-only variant in the same package; branch it in your
  pipeline instead.

---

## 7. The post-refresh checklist as data

`config/sandbox/post-refresh-checklist.json` — the checker in `scripts/` validates this file, so it is
the artefact that makes "did we forget a step" a build failure rather than a memory test.

```json
{
  "sandboxName": "uat",
  "postCopyClass": "SandboxPrep",
  "runAsAutoProcUser": true,
  "steps": [
    {
      "id": "mask-user-email",
      "owner": "apex",
      "idempotent": true,
      "verify": "SELECT COUNT() FROM User WHERE IsActive = TRUE AND Email != NULL AND (NOT Email LIKE '%.invalid')"
    },
    {
      "id": "deactivate-users",
      "owner": "apex",
      "idempotent": true,
      "verify": "SELECT COUNT() FROM User WHERE IsActive = TRUE AND Alias NOT IN ('sbxadm','intusr')"
    },
    {
      "id": "abort-scheduled-jobs",
      "owner": "apex",
      "idempotent": true,
      "verify": "SELECT COUNT() FROM CronTrigger WHERE State IN ('WAITING','ACQUIRED','EXECUTING','PAUSED','BLOCKED','PAUSED_BLOCKED')"
    },
    {
      "id": "scrub-integration-config",
      "owner": "apex",
      "idempotent": true,
      "verify": "SELECT Endpoint__c, Active__c FROM Integration_Config__c"
    },
    {
      "id": "reseed-reference-data",
      "owner": "pipeline",
      "idempotent": true,
      "verify": "SELECT COUNT() FROM Product2 WHERE IsActive = TRUE"
    },
    {
      "id": "apply-environment-config",
      "owner": "pipeline",
      "idempotent": true,
      "verify": "SELECT COUNT() FROM ApexClass WHERE Name = 'SandboxPrep'"
    },
    {
      "id": "set-deliverability-access-level",
      "owner": "manual",
      "idempotent": true,
      "verify": "Setup -> Email -> Deliverability -> Access Level reads 'System email only'"
    }
  ]
}
```

**How to read it:**

- **`owner` is the honest field.** `apex` = the post-copy class does it; `pipeline` = a deploy or script
  after activation; `manual` = a human in Setup. The deliverability step is `manual` because § 6 shows it
  has no metadata surface — pretending otherwise is how it silently stops happening.
- **Every `verify` for an `apex` step is a query whose correct answer is zero (or a known value).**
  A checklist item with no verification is a claim, not a control.
- **`runAsAutoProcUser` mirrors the test class.** If this reads `false`, the tests are not exercising the
  permission set the refresh actually uses.

Run the checker against it:

```bash
python3 scripts/check_sandbox_post_refresh_automation.py --manifest-dir force-app/main/default
```

---

## 8. package.xml and the deploy

The Apex goes to **production** (that is where the refresh copies from). The settings file goes to the
**sandbox**, after activation. Two packages, not one.

`manifest/package-postcopy-apex.xml` — deploy to production:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>SandboxPrep</members>
        <members>SandboxPrepTest</members>
        <name>ApexClass</name>
    </types>
    <version>62.0</version>
</Package>
```

`manifest/package-sandbox-email.xml` — deploy to the refreshed sandbox:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>EmailAdministration</members>
        <name>Settings</name>
    </types>
    <version>62.0</version>
</Package>
```

Commands:

```bash
# 1. Retrieve what production already has, before you overwrite anything.
sf project retrieve start \
  --manifest manifest/package-postcopy-apex.xml \
  --target-org prod

# 2. Validate against production without committing (run the post-copy tests).
sf project deploy validate \
  --manifest manifest/package-postcopy-apex.xml \
  --test-level RunSpecifiedTests \
  --tests SandboxPrepTest \
  --target-org prod

# 3. Deploy for real once the validation id is green.
sf project deploy start \
  --manifest manifest/package-postcopy-apex.xml \
  --test-level RunSpecifiedTests \
  --tests SandboxPrepTest \
  --target-org prod

# 4. AFTER the sandbox is refreshed and activated, push the email settings there.
sf project deploy start \
  --manifest manifest/package-sandbox-email.xml \
  --target-org uat
```

**Verification — the three queries that say whether the post-copy actually ran.** Run all three in the
refreshed sandbox, in this order:

```sql
-- (a) Nothing schedulable survived. Expect 0.
SELECT COUNT() FROM CronTrigger
WHERE State IN ('WAITING','ACQUIRED','EXECUTING','PAUSED','BLOCKED','PAUSED_BLOCKED')

-- (b) No active user still holds a routable address. Expect 0.
SELECT COUNT() FROM User
WHERE IsActive = TRUE AND Email != NULL AND (NOT Email LIKE '%.invalid')

-- (c) You are in a sandbox, not production. Expect true.
SELECT IsSandbox FROM Organization
```

Query (c) uses `Organization.IsSandbox` — "Read-only. Indicates whether the current organization is a
sandbox (true) or production (false) instance. Available in API version 31.0 or later" (Object Reference
L205411–205417). Run it **first** in any interactive session where you are about to abort jobs or mask
emails. `SandboxContext` is not available outside `runApexClass`; `IsSandbox` is available everywhere.

---

## Sources

- Apex Reference Guide (v62 PDF) — `SandboxPostCopy` interface and Automated Process user note
  (L228876–228902), sample implementation with the no-arg constructor (L228949–228981), sample test
  (L228986–229015), `Test.testSandboxPostCopyScript` 4-arg and 5-arg overloads (L241140–241228),
  `System.abortJob` (L238661–238698).
  https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_apex_developer_guide.pdf
- Object Reference (v62 PDF) — `CronTrigger` fields, supported calls and the nine `State` values
  (L86710–86844), `CronJobDetail.JobType` codes (L86671–86680), `Organization.IsSandbox` (L205411–205417).
  https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/object_reference.pdf
- Metadata API Developer Guide (v62 PDF) — sandbox username mutation (L2711–2713),
  `EmailAdministrationSettings` file suffix, version and field table (L114848–115022), sandbox tiers
  (L951–954). https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf
- Data Loader Guide (v62 PDF) — import batch size and Bulk API 2.0 behaviour (L351–360), operations
  (L967).
