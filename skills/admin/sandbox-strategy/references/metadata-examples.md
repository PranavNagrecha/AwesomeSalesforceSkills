# Metadata and API Examples: Sandbox Strategy

A sandbox strategy is mostly a decision document, but three parts of it are real,
deployable, version-controllable artifacts. This file holds those three, plus the two
tables the strategy document itself must contain.

| Part | Artifact | Where it lives |
|---|---|---|
| 1 | `SandboxSettings` — the only sandbox metadata type | `force-app/main/default/settings/Sandbox.settings` |
| 2 | A `SandboxPostCopy` Apex class + its test | `force-app/main/default/classes/` |
| 3 | `SandboxInfo` / `SandboxProcess` (Tooling API) — create, clone, refresh, monitor | API calls, not source files |
| 4 | Topology table + refresh calendar | the strategy document (`templates/sandbox-strategy-template.md`) |

---

## Part 1 — `SandboxSettings`: the only sandbox metadata type

`SandboxSettings` extends the `Metadata` metadata type, is stored in a single file named
`Sandbox.settings` in the `settings` folder, and is available in API version 56.0 and later
(Metadata API Developer Guide, `SandboxSettings`, api_meta.txt L125434–125446).

It has exactly one field:

| Field | Type | Meaning |
|---|---|---|
| `disableSandboxExpirationEmails` | boolean | Disables sandbox expiration email notifications **for the source (production) org**. When disabled, users no longer receive notifications for impending deletions of sandboxes inactive for 180 days or longer (api_meta.txt L125452–125458). |

### `force-app/main/default/settings/Sandbox.settings`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<SandboxSettings xmlns="http://soap.sforce.com/2006/04/metadata">
    <disableSandboxExpirationEmails>false</disableSandboxExpirationEmails>
</SandboxSettings>
```

**How to read it**

- The element name is `SandboxSettings`, the file name is `Sandbox.settings`. Settings files
  drop the `Settings` suffix from the file name (api_meta.txt L108368–108370).
- `false` is the deliberate value for most orgs. The notification is the only automatic
  warning that an inactive sandbox is heading for deletion at the 180-day mark. Set `true`
  only when a separate, owned process tracks sandbox inactivity — record who owns it in the
  strategy document.
- This is a **production-org** setting. Deploying it into a sandbox changes nothing that
  matters; the expiration emails it suppresses are sent from the source org.
- There is no metadata type for sandbox type, refresh cadence, template contents, or
  masking. Those are Setup and Tooling API surfaces, not source-controlled XML.

### `manifest/package.xml`

Settings are addressed through the `Settings` type name with the member being the component
name minus the `Settings` suffix (api_meta.txt L108362–108370).

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>Sandbox</members>
        <name>Settings</name>
    </types>
    <types>
        <members>PrepareSandbox</members>
        <members>PrepareSandboxTest</members>
        <name>ApexClass</name>
    </types>
    <version>62.0</version>
</Package>
```

The wildcard `*` does not apply to an individual feature setting — it applies only when
retrieving *all* settings (api_meta.txt L125471–125474). Name `Sandbox` explicitly.

### Retrieve and deploy

```bash
# Retrieve production's current sandbox settings before changing anything
sf project retrieve start --manifest manifest/package.xml --target-org prod

# Dry-run against production, then deploy
sf project deploy start --dry-run -d "force-app/main/default" --target-org prod
sf project deploy start --manifest manifest/package.xml --target-org prod
```

`sf project retrieve start --manifest path/to/package.xml` and
`sf project deploy start --dry-run -d "force-app/main/default" --target-org <alias>` are the
guide's own CLI forms (api_meta.txt L1348, L3985).

To authorize a sandbox rather than production, append the sandbox login URL
(REST API Developer Guide, api_rest.txt L1344–1346):

```bash
sf org login web --instance-url https://MyDomainName--UAT.sandbox.my.salesforce.com
```

**Verification step:** in the source org, Setup → Sandboxes. The expiration-notification
behaviour is not queryable through the Metadata API after deploy; confirm the deploy
succeeded with `sf project deploy report --use-most-recent` (api_meta.txt L96367) and then
confirm the Setup page reflects the intended value.

---

## Part 2 — The `SandboxPostCopy` class: what actually makes a refresh repeatable

> To make your sandbox environment business ready, automate data manipulation or business
> logic tasks. Extend this interface and add methods to perform post-copy tasks, then
> specify the class during sandbox creation.
> — Apex Reference Guide, `SandboxPostCopy Interface` (apexrefguide.txt L228876–228879)

The interface is in the `System` namespace and has one method
(apexrefguide.txt L228920–228938):

```apex
public void runApexClass(System.SandboxContext context)
```

`context` exposes `context.organizationId()`, `context.sandboxId()`, and
`context.sandboxName()` (apexrefguide.txt L228933–228937).

### The execution-context constraint that shapes every line of this class

> The `SandboxPostCopy` Apex class is executed at the end of the sandbox copy using a
> special Automated Process user that isn't visible within the org. This user doesn't have
> access to all objects and features; therefore, the Apex script cannot access all objects
> and features. If the script fails, run the script after sandbox activation as a user with
> appropriate permissions.
> — apexrefguide.txt L228889–228893

Two facts stack on top of that:

- Apex database operations run in **user mode** by default — they apply the sharing rules,
  FLS, and object permissions of the running user (Apex Developer Guide, apexdev.txt
  L11938–11941).
- **Automated Process users can't perform Object and FLS checks in custom code unless
  appropriate permission sets are explicitly applied to those users** (apexdev.txt L11921–11922).

So a post-copy class whose DML is left at the default access level is being permission-checked
against a user you cannot assign permission sets to through the normal Setup UI. Use
`as system` on DML statements (apexdev.txt L11976–11979) or the `AccessLevel.SYSTEM_MODE`
parameter on `Database` methods (apexdev.txt L11991–11994) for the scrub and seed operations.

### `force-app/main/default/classes/PrepareSandbox.cls`

```apex
/**
 * Post-copy script for every non-production environment in the sandbox ladder.
 * Registered on the sandbox record at create/refresh time (Setup > Sandboxes).
 *
 * Runs as the invisible Automated Process user at the end of the copy, so every
 * database operation here is pinned to system mode on purpose.
 * See references/gotchas.md, "Post-Copy Apex Runs as a User You Cannot Grant Anything To".
 */
global class PrepareSandbox implements SandboxPostCopy {

    // Implementations of SandboxPostCopy must have a no-arg constructor; the sandbox
    // copy process uses only this one (apexrefguide.txt L228952-228961).
    global PrepareSandbox() {}

    global void runApexClass(SandboxContext context) {
        System.debug('Post-copy start. Org: ' + context.organizationId()
            + ' Sandbox: ' + context.sandboxName()
            + ' (' + context.sandboxId() + ')');

        scrubContactEmails();
        seedEnvironmentSettings(context.sandboxName());
    }

    /**
     * Only the User object's Email field is suffixed with .invalid by the platform.
     * Contact, Lead and Person Account emails are copied verbatim, so they are scrubbed
     * here. See devops/sandbox-data-isolation-gotchas for the full inventory.
     */
    private void scrubContactEmails() {
        List<Contact> toScrub = [
            SELECT Id, Email
            FROM Contact
            WHERE Email != null AND (NOT Email LIKE '%.invalid')
            LIMIT 10000
        ];
        for (Contact c : toScrub) {
            c.Email = c.Email + '.invalid';
        }
        if (!toScrub.isEmpty()) {
            Database.update(toScrub, false, AccessLevel.SYSTEM_MODE);
        }
    }

    /**
     * Seeds the org-default row of a hierarchy Custom Setting that every integration
     * callout reads for its base URL, so no endpoint in the refreshed sandbox still
     * points at a production system.
     */
    private void seedEnvironmentSettings(String sandboxName) {
        Environment_Config__c cfg = Environment_Config__c.getOrgDefaults();
        cfg.Environment_Name__c = sandboxName;
        cfg.Is_Production__c = false;
        cfg.Integration_Base_Url__c = 'https://stub.internal.invalid';
        upsert as system cfg;
    }
}
```

**How to read it**

- `global` on the class and on `runApexClass` matches the guide's own sample
  (apexrefguide.txt L228952, L228975).
- The no-arg constructor is mandatory. The guide's sample also shows an arg constructor and
  states plainly that the copy process won't use it (apexrefguide.txt L228955–228959) — this
  version omits it rather than shipping a constructor nothing calls.
- `Database.update(..., false, AccessLevel.SYSTEM_MODE)` is partial-success on purpose: one
  unwritable Contact should not abort the scrub of the other 9,999.
- `Environment_Config__c` is a placeholder for your org's own configuration Custom Setting.
  Replace the API names; the pattern — a hierarchy setting's org-default row rewritten to
  environment-safe values — is the transferable part.
- **Email deliverability is not set here.** UNVERIFIED (2026-09-04): none of the API guides
  consulted (Metadata API, Apex Developer Guide, Apex Reference Guide, REST API) expose the
  Setup → Deliverability access level as a writable property, and `devops/sandbox-data-isolation-gotchas`
  states the setting is not writable through Apex or Metadata API. Treat verifying it as a
  manual first item in the post-refresh runbook, not something this class can do.
- The `LIMIT 10000` is a deliberate ceiling for the synchronous post-copy context. On a Full
  sandbox with millions of Contacts, this class should enqueue a Batch or Queueable job
  instead of scrubbing inline.

### `force-app/main/default/classes/PrepareSandboxTest.cls`

Test with `System.Test.testSandboxPostCopyScript()` (apexrefguide.txt L228943–228945). Use
the five-argument overload with `RunAsAutoProcUser = true` — Salesforce explicitly
recommends it over the four-argument form, because it tests the script with the same user
access permissions used by post-copy tasks during sandbox creation and so uncovers the
permission failures the four-argument form hides (apexrefguide.txt L241180–241186,
L241225–241232).

```apex
@isTest
private class PrepareSandboxTest {

    @isTest
    static void postCopyScrubsContactEmailsAndSeedsConfig() {
        Contact c = new Contact(LastName = 'Rivera', Email = 'real.person@example.com');
        insert c;

        Test.startTest();
        // Five-arg overload: RunAsAutoProcUser = true runs the script with the same
        // permissions post-copy tasks use during sandbox creation.
        Test.testSandboxPostCopyScript(
            new PrepareSandbox(),
            UserInfo.getOrganizationId(),
            UserInfo.getOrganizationId(),
            'UAT',
            true
        );
        Test.stopTest();

        Contact scrubbed = [SELECT Email FROM Contact WHERE Id = :c.Id];
        System.assertEquals('real.person@example.com.invalid', scrubbed.Email,
            'Post-copy must suffix Contact emails so refreshed sandboxes cannot mail real people');

        Environment_Config__c cfg = Environment_Config__c.getOrgDefaults();
        System.assertEquals('UAT', cfg.Environment_Name__c, 'Sandbox name must be seeded');
        System.assertEquals(false, cfg.Is_Production__c, 'Refreshed sandbox must not claim to be production');
    }
}
```

`testSandboxPostCopyScript` throws a run-time exception if the test install fails
(apexrefguide.txt L241173). The guide's own sample passes `UserInfo.getOrganizationId()`
for the org id and a literal for the sandbox id (apexrefguide.txt L229002–229006).

**Deploy note:** by default, **no tests are run in a deployment to a non-production org**
such as a sandbox or Developer Edition org (api_meta.txt L2659–2661). A green sandbox deploy
therefore proves nothing about production test coverage. Set the test level explicitly:

```bash
sf project deploy start --manifest manifest/package.xml \
  --target-org uat --test-level RunLocalTests
```

`RunLocalTests` is enforced regardless of package contents, and is valid for both sandbox and
production deployments (api_meta.txt L2677–2679).

---

## Part 3 — `SandboxInfo` and `SandboxProcess`: create, clone, refresh, monitor

The Apex Reference Guide's `SandboxPostCopy` page points at `Tooling API: SandboxInfo` and
`Tooling API: SandboxProcess` as the companion surfaces (apexrefguide.txt L228902–228903).
`SandboxInfo` is the definition record — one per sandbox; `SandboxProcess` is the row per
copy operation, which is what you poll.

> UNVERIFIED (2026-09-04): these two objects live in the **Tooling API**, and the Tooling API
> Developer Guide is not among the sources available for this pass. They appear in the Object
> Reference, Metadata API, REST API and Apex guides only as the cross-reference above. The
> field names below (`LicenseType`, `TemplateId`, `AutoActivate`, `ApexClassId`, `SourceId`,
> `Status`, `CopyProgress`) are therefore **not verified against a primary source here**.
> Confirm each against the Tooling API Developer Guide for your API version before running
> any of this against a real org. The request *shapes* — REST base path, POST-to-create,
> response body — are grounded; the *field vocabulary* is not.

The Tooling API base path is `/services/data/vXX.X/tooling` (api_rest.txt L7718). Records are
created by POSTing the field values as JSON to the sObject Basic Information resource, and the
response body carries the new record's id (api_rest.txt L2698–2712).

### Create a Developer Pro sandbox with auto-activation and a post-copy class

```bash
curl https://MyDomainName.my.salesforce.com/services/data/v62.0/tooling/sobjects/SandboxInfo/ \
  -H "Authorization: Bearer token" \
  -H "Content-Type: application/json" \
  -d "@newsandbox.json"
```

`newsandbox.json`:

```json
{
  "SandboxName": "DevPro1",
  "LicenseType": "DEVELOPER_PRO",
  "Description": "Shared config + integration build environment for the CRM stream",
  "AutoActivate": true,
  "ApexClassId": "01p5f000000XyZaAAK"
}
```

Successful response (api_rest.txt L2717–2723):

```json
{
  "id": "0GQ5f000000XyZbGAK",
  "errors": [],
  "success": true
}
```

- `AutoActivate: true` activates the sandbox as soon as the copy finishes, instead of leaving
  it waiting for someone to click Activate. Use it for the environments in your refresh
  calendar; leave it off when a human must inspect before anyone logs in.
- `ApexClassId` is the id of the `PrepareSandbox` class from Part 2. Retrieve it first:
  `SELECT Id FROM ApexClass WHERE Name = 'PrepareSandbox'`.

### Clone an existing sandbox instead of copying production

```json
{
  "SandboxName": "UATFix",
  "LicenseType": "DEVELOPER_PRO",
  "SourceId": "0GQ5f000000XyZbGAK",
  "AutoActivate": true,
  "ApexClassId": "01p5f000000XyZaAAK"
}
```

`SourceId` points at the `SandboxInfo` record of the sandbox to clone. A clone reproduces
another sandbox's state, not production's — which is exactly what you want when reproducing a
UAT defect without disturbing UAT, and exactly what you do not want when you need production
parity.

### Refresh: update the existing record, do not create a new one

A refresh is a PATCH to the **same** `SandboxInfo` record. There is no separate refresh
resource, and creating a second `SandboxInfo` with the same name is not a refresh — it
consumes another license.

```bash
curl -X PATCH \
  https://MyDomainName.my.salesforce.com/services/data/v62.0/tooling/sobjects/SandboxInfo/0GQ5f000000XyZbGAK \
  -H "Authorization: Bearer token" \
  -H "Content-Type: application/json" \
  -d '{"AutoActivate": true, "ApexClassId": "01p5f000000XyZaAAK", "TemplateId": "0TT5f000000XyZcGAK"}'
```

`TemplateId` selects the sandbox template that decides which objects' data is copied. It is
required for a Partial Copy and is the reason the Create action for a Partial Copy does not
appear until a template exists (see SKILL.md, "What Your Org Actually Owns").

### Monitor the copy

Poll `SandboxProcess` — one row per copy operation, so order by creation date and take the
newest for a given sandbox:

```sql
SELECT Id, SandboxName, Status, CopyProgress, SandboxInfoId,
       CreatedDate, EndDate, ActivatedDate
FROM SandboxProcess
WHERE SandboxName = 'DevPro1'
ORDER BY CreatedDate DESC
LIMIT 1
```

Run it against the Tooling API, not the standard query endpoint:

```bash
curl -G https://MyDomainName.my.salesforce.com/services/data/v62.0/tooling/query/ \
  -H "Authorization: Bearer token" \
  --data-urlencode "q=SELECT Id, SandboxName, Status, CopyProgress FROM SandboxProcess WHERE SandboxName = 'DevPro1' ORDER BY CreatedDate DESC LIMIT 1"
```

**Verification step:** the copy is done when the newest `SandboxProcess` row for that name
reaches a completed status *and* the post-copy class has left its trace. Because the
Automated Process user's debug output is easy to lose, assert on data rather than logs — in
the new sandbox, run:

```sql
SELECT COUNT() FROM Contact WHERE Email != null AND (NOT Email LIKE '%.invalid')
```

A non-zero count means `PrepareSandbox` did not complete, whatever the process status says.
Re-run it manually as a user with appropriate permissions, which is the guide's own remedy
for a failed post-copy script (apexrefguide.txt L228892–228893).

---

## Part 4 — The two tables the strategy document must carry

### Topology table

Purpose drives type; type constrains cadence. Storage and refresh-interval figures are the
published limits recorded in SKILL.md ("Type Capacities and Refresh Windows") and sourced in
`references/well-architected.md`.

| Environment | Type | Purpose | Data | Refresh floor | Cadence | Post-copy class | Owner |
|---|---|---|---|---|---|---|---|
| `DEV-<initials>` | Developer | Individual build work | Metadata + 200 MB | 1 day | On demand | `PrepareSandbox` | each developer |
| `INT` | Developer Pro | Shared integration branch | Metadata + 1 GB, seeded | 1 day | Per sprint | `PrepareSandbox` | release manager |
| `QA` | Partial Copy | Regression with sampled production data | Template-selected objects, 5 GB | 5 days | Per sprint | `PrepareSandbox` | QA lead |
| `UAT` | Full | Business validation and production rehearsal | Full production copy | 29 days | Per release | `PrepareSandbox` | release manager |
| `TRAIN` | Developer Pro | Training environment | Curated demo data | 1 day | Per training cycle | `PrepareSandbox` | enablement |

Rules the table is enforcing:

- Production never appears as a build target. If it does, the strategy is not a strategy.
- Two Full sandboxes need a written justification, because a Full license can provision any
  lower type (SKILL.md, "Higher-tier licenses substitute downward") and a second Full is
  usually a Partial Copy that nobody costed.
- Every row with production data has a post-copy class, not a note saying "mask manually".
- The refresh floor column is a hard platform floor. A cadence shorter than the floor is a
  wish, not a plan.

### Refresh calendar shape

The calendar's job is to make the 29-day Full floor collide visibly with the release
schedule *before* the release, not during it.

| Week | DEV-* | INT | QA | UAT | Notes |
|---|---|---|---|---|---|
| Sprint 1, wk 1 | on demand | refresh Mon | — | — | INT reset from prod at sprint open |
| Sprint 1, wk 2 | on demand | — | refresh Mon | — | QA seeded from Partial Copy template |
| Sprint 2, wk 1 | on demand | refresh Mon | — | — | |
| Sprint 2, wk 2 | on demand | — | refresh Mon | — | |
| Release wk −4 | on demand | — | — | **refresh** | Full floor: next UAT refresh no earlier than release wk 0 |
| Release wk −2 | frozen | frozen | regression | UAT sign-off | no refreshes during the freeze |
| Release wk 0 | — | — | — | — | deploy to production |
| Release wk +1 | refresh all | refresh | refresh | eligible again | post-release reset |

Every refresh cell in this calendar implies the post-refresh runbook in
`templates/sandbox-strategy-template.md` runs to completion before the environment is handed
back. A refresh is not finished when the copy finishes.

Simultaneous refresh requests are processed in series, one at a time, not in parallel
(SKILL.md, "Salesforce-Specific Gotchas") — which is why no two environments share a refresh
cell in the same week without a note saying which one goes first.
