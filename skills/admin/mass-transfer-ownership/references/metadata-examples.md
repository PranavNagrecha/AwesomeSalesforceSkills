# Operational Artifacts — Mass Transfer Ownership

A mass transfer produces almost no object metadata. What it produces is a **run kit**: an
impact query set, a job payload, a rollback CSV, and a verification query set. The one piece
of deployable metadata a transfer ever needs is `Sharing.settings` — the two defer flags that
hold sharing recalculation back while the write lands.

Everything below is a copy-and-edit artefact. Replace `005…` / `00G…` / `v62.0` before use.

---

## 1. Pre-transfer impact query set

Run all seven before you decide the tool. Each answers a question the runbook depends on.

### 1a. Volume by owner and object

```sql
SELECT OwnerId, Owner.Name, COUNT(Id) recordCount
FROM   Account
WHERE  OwnerId IN ('005XX0000012aBcAAI', '005XX0000012aBdAAI')
GROUP BY OwnerId, Owner.Name
ORDER BY COUNT(Id) DESC
```

Repeat per object in scope. Above 2,000 rows in a single object the Bulk API is the right
tool: "Any data operation that includes more than 2,000 records is a good candidate for Bulk
API 2.0 … Jobs with fewer than 2,000 records should involve 'bulkified' synchronous calls in
REST (for example, Composite) or SOAP" (App Limits, *Bulk API and Bulk API 2.0 Limits and
Allocations*).

### 1b. Open vs closed — decide what actually has to move

```sql
SELECT IsClosed, StageName, COUNT(Id)
FROM   Opportunity
WHERE  OwnerId = '005XX0000012aBcAAI'
GROUP BY IsClosed, StageName
ORDER BY IsClosed
```

Closed-won Opportunities usually stay with the historical owner for commission attribution.
Splitting the file on `IsClosed` early is cheaper than reversing it later.

### 1c. Records that carry a team

```sql
SELECT Opportunity.Id, Opportunity.Name, COUNT(Id) teamSize
FROM   OpportunityTeamMember
WHERE  Opportunity.OwnerId = '005XX0000012aBcAAI'
GROUP BY Opportunity.Id, Opportunity.Name

SELECT AccountId, COUNT(Id) teamSize
FROM   AccountTeamMember
WHERE  Account.OwnerId = '005XX0000012aBcAAI'
GROUP BY AccountId
```

These are the rows where the transfer has a *second* effect beyond `OwnerId`. See §4 for what
the Object Reference says happens to each.

### 1d. Queue-owned rows (they need a `00G` target, not `005`)

```sql
SELECT Id, Name, Type
FROM   Group
WHERE  Type = 'Queue'
ORDER BY Name

SELECT Id, CaseNumber, OwnerId
FROM   Case
WHERE  OwnerId IN (SELECT Id FROM Group WHERE Type = 'Queue')
```

`Group.Type` is a restricted picklist whose values include `Queue` — "Public group that
includes all the User records that are members of a queue" (Object Reference, `Group.Type`).

### 1e. Which objects can even hold a queue owner

`Case.OwnerId` is documented as a polymorphic relationship field that **Refers To: Group,
User**. `Account.OwnerId` is documented as **Refers To: User** only (Object Reference,
`Account` and `Case` field tables). Check the field table for every object in scope before you
put a `00G` id in the file.

### 1f. Child counts that will *not* follow the parent

```sql
SELECT COUNT(Id) FROM Case        WHERE Account.OwnerId = '005XX0000012aBcAAI'
SELECT COUNT(Id) FROM Contact     WHERE Account.OwnerId = '005XX0000012aBcAAI'
SELECT COUNT(Id) FROM Opportunity WHERE Account.OwnerId = '005XX0000012aBcAAI'
```

Every non-zero count here is a separate Bulk job you have not planned yet.

### 1g. Can the *running* user actually transfer these rows?

```sql
SELECT RecordId, HasTransferAccess, MaxAccessLevel
FROM   UserRecordAccess
WHERE  UserId = '005XX0000012aBcAAI'
AND    RecordId IN ('001XX000003DHP0AAO', '001XX000003DHP1AAO')
```

Two hard constraints, both documented:

- "To change ownership of a record by updating its `OwnerId` field, you must have both the
  Transfer Record permission and Read access to the User record of the new record owner"
  (Object Reference, `User` usage notes).
- `UserRecordAccess` caps at **200 record IDs per query** and "doesn't consider whether a
  user's access is blocked due to a restriction rule" (Object Reference, `UserRecordAccess`
  usage). Sample 200 representative rows; do not try to run the whole file through it.

---

## 2. Bulk API 2.0 update job — the OwnerId write

### 2a. Create the job

`POST /services/data/v62.0/jobs/ingest`

```json
{
  "object": "Account",
  "operation": "update",
  "contentType": "CSV",
  "columnDelimiter": "COMMA",
  "lineEnding": "LF"
}
```

Header/setting choices, and why each is what it is:

| Choice | Value here | Grounding |
|---|---|---|
| `assignmentRuleId` | **omitted** | Optional property, "The ID of an assignment rule to run for a Case or a Lead" (Bulk API 2.0, *Create a Job* request body). Omitting it is how you keep assignment rules from re-routing what you just moved. |
| `operation` | `update` | Valid values are `insert`, `delete`, `hardDelete`, `update`, `upsert` (same table). Never `upsert` for a transfer — an id typo becomes an insert. |
| `object` | one per job | "Use only a single object type per job" (same table). Parent and child are always separate jobs. |
| `lineEnding` | `LF` | Default is `LF`; the only other value is `CRLF` (same table). Set it explicitly so a Windows-authored CSV doesn't silently mis-parse. |
| notify the new owner | **not possible here** | The *Create a Job* request body has exactly six properties — `assignmentRuleId`, `columnDelimiter`, `contentType`, `externalIdFieldName`, `lineEnding`, `object`, `operation`. There is no email header. The Apex Reference is explicit about the consequence: "If you use the API to change record ownership, or if a Lightning Experience user changes a record's owner, no email notification is sent. To send email notifications to a record's new owner, set the `triggerUserEmail` property to true" — and `triggerUserEmail` lives on `Database.DMLOptions.EmailHeader`, which "take[s] effect only for DML operations carried out in Apex code". **If the business requires the new-owner email, the transfer must run through Apex (§4), not Bulk API.** |
| "transfer open activities" | **not available on this path** | UNVERIFIED (2026-09-04): the Setup Mass Transfer wizard's *transfer open activities / notes / attachments* checkboxes are not described in any of the v62 PDFs used here (Object Reference, Metadata API, Apex, Data Loader, Bulk API, App Limits, REST API). What the Object Reference *does* document is `OwnerChangeOptionInfo` — "Represents default and optional actions that can be performed when a record's owner is changed. Available in API version 35.0 and later, but to query for change owner metadata, use the OwnerChangeOptionInfo object in Tooling API instead." Query that object in your own org to see which options your objects expose; do not assume the wizard's checkbox set. |

### 2b. Upload the CSV

`PUT {contentUrl}` with `Content-Type: text/csv`

```csv
Id,OwnerId
001XX000003DHP0AAO,005XX0000012aBdAAI
001XX000003DHP1AAO,005XX0000012aBdAAI
001XX000003DHP2AAO,005XX0000012aBdAAI
```

Two columns only. Every extra column is another field you are silently overwriting.

### 2c. Close the job

`PATCH /services/data/v62.0/jobs/ingest/{jobId}`

```json
{ "state": "UploadComplete" }
```

### 2d. The allocations this job consumes

| Limit | Value | Source |
|---|---|---|
| Batches per rolling 24 h (shared with Bulk API 1.0) | 15,000 | App Limits, *Batch Allocations* |
| Records uploaded per rolling 24 h | 150,000,000 | App Limits, *Limits Specific to Ingest Jobs* |
| Batching | "Salesforce creates a separate batch for every 10,000 records in your job data" | Bulk API 2.0 Developer Guide |
| Max file size per job | 150 MB; upload ≤100 MB because base64 conversion "can increase the data size by approximately 50%" | App Limits, *Limits Specific to Ingest Jobs* |
| Results retrievable for | 7 days after job completion | App Limits, *Results lifespan* |

A 47,000-row Account transfer is 5 batches. The 15,000-batch ceiling is not your problem; the
7-day results window is — pull `successfulResults` and `failedResults` the same day.

---

## 3. Data Loader `process-conf.xml` — the same update, headless

Excerpt from `process-conf.xml`; the real file's root element is `<beans>` and holds one
`<bean>` per job. Shaped from the Data Loader Guide's own `accountInsert` sample.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!-- EXCERPT: one bean from process-conf.xml. The real file contains several
     sibling <bean> elements under this same <beans> root. -->
<beans>
    <bean id="accountOwnerTransfer"
          class="com.salesforce.dataloader.process.ProcessRunner"
          scope="prototype">
        <description>Reassigns Account.OwnerId from the departing rep to the target owner.</description>
        <property name="name" value="accountOwnerTransfer"/>
        <property name="configOverrideMap">
            <map>
                <entry key="sfdc.endpoint" value="https://MyDomainName.my.salesforce.com"/>
                <entry key="sfdc.username" value="admin@example.org"/>
                <entry key="process.encryptionKeyFile" value="C:\Users\admin\.dataloader\dataLoader.key"/>
                <entry key="sfdc.password" value="ENCRYPTED_WITH_encrypt.bat"/>
                <entry key="sfdc.timeoutSecs" value="600"/>
                <entry key="sfdc.loadBatchSize" value="200"/>
                <entry key="sfdc.entity" value="Account"/>
                <entry key="process.operation" value="update"/>
                <entry key="process.mappingFile" value="C:\transfer\accountOwnerTransfer.sdl"/>
                <entry key="dataAccess.name" value="C:\transfer\in\account_owner_transfer.csv"/>
                <entry key="dataAccess.type" value="csvRead"/>
                <entry key="process.outputSuccess" value="C:\transfer\log\accountOwnerTransfer_success.csv"/>
                <entry key="process.outputError" value="C:\transfer\log\accountOwnerTransfer_error.csv"/>
            </map>
        </property>
    </bean>
</beans>
```

Run it: `process.bat "C:\transfer\config" accountOwnerTransfer` — first argument is the
directory holding `process-conf.xml`, second is the bean id (Data Loader Guide, *Run in Batch
Mode*). **The Data Loader command-line interface is supported for Windows only.**

Settings this excerpt deliberately does *not* set:

- **No assignment rule.** The Settings dialog's *Assignment rule* field takes "the ID of the
  assignment rule to use for inserts, updates, and upserts … on cases and leads", and the
  guide states plainly: "**The assignment rule overrides Owner values in your CSV file.**"
  On a Case or Lead transfer, leaving an assignment rule id in place silently discards the
  `OwnerId` column you just built.
- **No Bulk API.** `sfdc.loadBatchSize` of 200 is the SOAP path. Switching to Bulk API 2.0
  changes two behaviours: empty field values are ignored ("To set a field value to null when
  either API option is selected, use a field value of `#N/A` in the import CSV file"), and it
  is incompatible with Keep Account Teams — see the gotchas file.

### Keep Account Teams (Account transfers only)

`config.properties`, with Data Loader **closed**:

```properties
sfdc.useBulkApi=false
process.keepAccountTeam=true
```

Requires Data Loader 56.0.3 or later. The guide's constraint on the file is absolute: "the
uploaded .csv file must have the same value for all Current Account owner records. Likewise,
the New Account Owner records must all have the same value. Otherwise, the operation fails and
the Account Owners are not updated." A many-to-many territory remap therefore cannot use this
switch in one pass — it needs one file (and one run) per old-owner/new-owner pair.

---

## 4. Batch Apex — transfer with `Database.DMLOptions` and a rollback log

Use this path when the transfer needs conditional logic, the new-owner email, or explicit
control over which side effects fire. `Database.DMLOptions` "take[s] effect only for record
operations performed using Apex DML and not through the Salesforce user interface" — and, by
the same token, not through Bulk API.

```apex
/**
 * Reassigns OwnerId for a scoped set of records and writes the rollback pairs
 * as it goes. Governed by Database.DMLOptions rather than tool defaults.
 *
 * Documented ownership-change side effects this class does NOT suppress —
 * they are platform behaviour, not options:
 *   Opportunity: "If you update this field, the previous owner's access becomes
 *     Read Only or the access specified in your organization-wide default for
 *     opportunities, whichever is greater." (Object Reference, Opportunity.OwnerId)
 *   Opportunity teams: "For API version 12.0 and later, sharing records are kept,
 *     as they are for all objects. (All previous opportunity team members are kept
 *     on the opportunity team.)" — so via the API the previous owner stays on the
 *     team; the UI instead lets you pick their access level. (Object Reference,
 *     Opportunity.OwnerId + OpportunityTeamMember usage note)
 *   Account teams: "If team members are added by a user with group-based access,
 *     those members are removed after an account's owner is changed. This applies
 *     even if the Keep account team option is selected." (Object Reference,
 *     AccountTeamMember usage note)
 *   Every row re-enters the save order: before-save flows (3), before triggers (4),
 *     validation rules (5), duplicate rules (6), after triggers (8), assignment
 *     rules (9), workflow (11), after-save flows (14), Criteria Based Sharing
 *     evaluation (18). (Apex Developer Guide, Triggers and Order of Execution)
 */
public class OwnerTransferBatch implements Database.Batchable<SObject>, Database.Stateful {

    private final String  soql;
    private final Id      newOwnerId;
    private final Boolean notifyNewOwner;

    // Rollback log: recordId -> owner the record had before this run.
    public Map<Id, Id> previousOwnerById = new Map<Id, Id>();
    public Integer failureCount = 0;

    public OwnerTransferBatch(String soql, Id newOwnerId, Boolean notifyNewOwner) {
        this.soql           = soql;           // must select Id, OwnerId
        this.newOwnerId     = newOwnerId;
        this.notifyNewOwner = notifyNewOwner;
    }

    public Database.QueryLocator start(Database.BatchableContext bc) {
        return Database.getQueryLocator(soql);
    }

    public void execute(Database.BatchableContext bc, List<SObject> scope) {
        List<SObject> toUpdate = new List<SObject>();

        for (SObject record : scope) {
            Id currentOwner = (Id) record.get('OwnerId');
            if (currentOwner == newOwnerId) {
                continue;                                  // already there; skip the DML
            }
            previousOwnerById.put((Id) record.get('Id'), currentOwner);
            record.put('OwnerId', newOwnerId);
            toUpdate.add(record);
        }
        if (toUpdate.isEmpty()) {
            return;
        }

        Database.DMLOptions dmlo = new Database.DMLOptions();

        // Partial success: one bad row must not discard the batch.
        // "If optAllOrNone is set to false and a record fails, the remainder of the
        //  DML operation can still succeed." (Apex Reference, DmlOptions.optAllOrNone)
        dmlo.optAllOrNone = false;

        // The API sends no owner-change email unless you ask for one.
        dmlo.EmailHeader.triggerUserEmail = notifyNewOwner;

        // assignmentRuleHeader is deliberately left unset. Setting useDefaultRule
        // would run the default Case/Lead assignment rule and can re-route the very
        // records being transferred. Note it is cases and leads only:
        // "The Database.DMLOptions object supports assignment rules for cases and
        //  leads, but not for accounts." (Apex Reference, assignmentRuleHeader)

        List<Database.SaveResult> results = Database.update(toUpdate, dmlo);

        for (Integer i = 0; i < results.size(); i++) {
            if (!results[i].isSuccess()) {
                failureCount++;
                Id failedId = toUpdate[i].Id;
                previousOwnerById.remove(failedId);        // never log a rollback we didn't cause
                for (Database.Error err : results[i].getErrors()) {
                    System.debug(LoggingLevel.ERROR,
                        'OwnerTransfer failed ' + failedId + ': ' +
                        err.getStatusCode() + ' ' + err.getMessage());
                }
            }
        }
    }

    public void finish(Database.BatchableContext bc) {
        System.debug(LoggingLevel.INFO,
            'OwnerTransferBatch: ' + previousOwnerById.size() + ' transferred, ' +
            failureCount + ' failed. Persist previousOwnerById as the rollback CSV.');
    }
}
```

Invoke with an explicit scope:

```apex
String q = 'SELECT Id, OwnerId FROM Opportunity ' +
           'WHERE OwnerId = \'005XX0000012aBcAAI\' AND IsClosed = false';
Database.executeBatch(new OwnerTransferBatch(q, '005XX0000012aBdAAI', false), 200);
```

Scope rules, from the Apex Developer Guide's batch limits:

- "If no size is specified with the optional scope parameter of `Database.executeBatch`,
  Salesforce chunks the records returned by the start method into batches of 200 records."
- With a `QueryLocator`, scope "can have a maximum value of 2,000 … The optimal scope size is
  a factor of 2000, for example, 100, 200, 400 and so on."
- "A maximum of 50 million records can be returned in the `Database.QueryLocator` object. If
  more than 50 million records are returned, the batch job is immediately terminated and
  marked as Failed."

Above roughly 100k rows, drop scope to 100 rather than raising it: every record in a chunk
re-runs the full save order plus Criteria Based Sharing evaluation in one transaction.

---

## 5. The one deployable metadata file: deferred sharing recalculation

`SharingSettings` carries two flags that suspend recalculation while the transfer runs. It is
a settings type, so the file is `settings/Sharing.settings` and the manifest member is
`Sharing` under `Settings`.

`force-app/main/default/settings/Sharing.settings-meta.xml`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<SharingSettings xmlns="http://soap.sforce.com/2006/04/metadata">
    <deferGroupMembership>true</deferGroupMembership>
    <deferSharingRules>true</deferSharingRules>
</SharingSettings>
```

`manifest/package.xml`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>Sharing</members>
        <name>Settings</name>
    </types>
    <version>62.0</version>
</Package>
```

Commands:

```bash
# Capture the current state before you change anything — this IS the rollback.
sf project retrieve start --metadata "Settings:Sharing" --target-org prod

# Suspend recalculation immediately before the transfer window.
sf project deploy start --manifest manifest/package.xml --target-org prod

# After the transfer, flip both flags back to false and redeploy to resume.
sf project deploy start --manifest manifest/package.xml --target-org prod
```

### How to read it

- **`deferGroupMembership`** — "Indicates whether group membership calculations are suspended
  (true) or not (false)… available in API version 49.0 and later."
- **`deferSharingRules`** — "Indicates whether sharing rule calculations are suspended (true)
  or not (false)… available in API version 49.0 and later."
- **The feature is off until you ask for it.** "The defer sharing calculation feature isn't
  enabled by default. To enable it for your Salesforce org, contact Salesforce Customer
  Support." Raise that case *weeks* before the transfer window, not the night before.
- **The flags are ordered.** "If the `deferGroupMembership` field is set to true, you can't
  change the value of `deferSharingRules`. Sharing rule calculations are suspended regardless
  of the value of `deferSharingRules`." So suspend group membership last and resume it first.
- **Resuming is the expensive half.** "When you change the value of this field from true to
  false, sharing rules are automatically recalculated. Depending on your org, this
  recalculation can take a significant amount of time to complete." The transfer finishes in
  minutes; the resume is what needs the maintenance window.
- **Deploying this file touches org-wide sharing.** Retrieve first (command above) so the
  pre-transfer values are in source control, and deploy only the two elements you intend to
  change — a full `Sharing.settings` retrieved from a different org will carry a dozen other
  flags with it.
- **Permission required:** "To use SharingSettings, you need the Manage Sharing permission."

### Verification step

```sql
SELECT Id, Name FROM AsyncApexJob WHERE Status IN ('Queued','Processing') LIMIT 1
```

and in Setup → **Environments → Jobs → Background Jobs**, confirm no
*Sharing Rule Recalculation* rows remain before you declare the transfer complete. The
deploy returning `Succeeded` only means the flag flipped, not that recalculation drained.

---

## 6. Post-transfer verification query set

```sql
-- 1. The source owners must hold nothing in scope. Expect 0.
SELECT COUNT(Id)
FROM   Account
WHERE  OwnerId IN ('005XX0000012aBcAAI', '005XX0000012aBdAAI')

-- 2. The target holds exactly what the plan said. Compare to the §1a count.
SELECT OwnerId, COUNT(Id)
FROM   Account
WHERE  OwnerId = '005XX0000012aBeAAI'
GROUP BY OwnerId

-- 3. Children did NOT silently follow (or did, if you ran their job).
SELECT OwnerId, COUNT(Id)
FROM   Case
WHERE  AccountId IN (SELECT Id FROM Account WHERE OwnerId = '005XX0000012aBeAAI')
GROUP BY OwnerId

-- 4. Nothing landed on an inactive user.
SELECT Id, Name, IsActive
FROM   User
WHERE  Id IN ('005XX0000012aBeAAI')
AND    IsActive = false

-- 5. Teams survived the move (compare to the §1c baseline).
SELECT AccountId, COUNT(Id)
FROM   AccountTeamMember
WHERE  Account.OwnerId = '005XX0000012aBeAAI'
GROUP BY AccountId

-- 6. The new owner can actually work the records (200-id sample).
SELECT RecordId, HasReadAccess, HasEditAccess, HasTransferAccess, MaxAccessLevel
FROM   UserRecordAccess
WHERE  UserId = '005XX0000012aBeAAI'
AND    RecordId IN ('001XX000003DHP0AAO', '001XX000003DHP1AAO')
```

Query 6 is the one that catches a recalculation that has not drained: `HasReadAccess = false`
for the *owner* means the share rows are still being written.

---

## 7. Rollback plan

The rollback artefact is a CSV captured **before** the update, not reconstructed after it.

### Capture (before anything is written)

```sql
SELECT Id, OwnerId
FROM   Account
WHERE  OwnerId IN ('005XX0000012aBcAAI', '005XX0000012aBdAAI')
```

Export, and rename the `OwnerId` column to `Old_OwnerId`. The plan file becomes:

```csv
Id,OwnerId,Old_OwnerId
001XX000003DHP0AAO,005XX0000012aBeAAI,005XX0000012aBcAAI
001XX000003DHP1AAO,005XX0000012aBeAAI,005XX0000012aBcAAI
001XX000003DHP2AAO,005XX0000012aBeAAI,005XX0000012aBdAAI
```

Lint it before the run:

```bash
python3 scripts/check_mass_transfer_ownership.py --plan transfer-plan.csv --max-rows 10000
```

### Reverse

Rebuild the same file with `Old_OwnerId` mapped into the `OwnerId` column and re-run the
identical job. Nothing else about the run changes.

```csv
Id,OwnerId
001XX000003DHP0AAO,005XX0000012aBcAAI
001XX000003DHP1AAO,005XX0000012aBcAAI
001XX000003DHP2AAO,005XX0000012aBdAAI
```

### What rollback does *not* undo

| Side effect | Reversible by re-running the CSV? |
|---|---|
| `OwnerId` value | Yes |
| `Owner` share rows (`RowCause = Owner`) | Yes, but asynchronously — recalculation runs again |
| Account team members removed because they were added by a group-access user | **No.** They are gone; re-add them from the §1c baseline. |
| Emails already sent (`triggerUserEmail = true`) | No |
| Records re-routed by an assignment rule that fired during the run | **No** — the rule wrote a third owner, and your `Old_OwnerId` is now wrong for those rows |
| Downstream automation that fired on owner change (tasks created, integrations notified) | No |

That last block is the argument for a sandbox rehearsal: the rollback CSV covers the field,
not the consequences.

---

## Cross-references

- Bulk API job mechanics and batch sizing → `data/bulk-api-and-large-data-loads`,
  `data/data-loader-and-tools`
- Territory realignment, which is a different operation entirely →
  `admin/enterprise-territory-management`
- The sharing model this transfer perturbs → `admin/sharing-and-visibility`
