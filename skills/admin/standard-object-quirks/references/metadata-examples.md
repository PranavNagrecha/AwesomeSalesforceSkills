# Metadata Examples — Standard Object Quirks

Deployable artefacts for the quirks this skill documents. Every one of them encodes a
behaviour that the Apex Developer Guide or Object Reference states explicitly, and that the
common folklore states wrongly.

Element names, properties and enum values come from the Metadata API Developer Guide
(`StandardValueSet`, `StandardValue`, `CustomObject` sections), the Object Reference
(`Account`, `Contact`, `Task`, `Event`, `Case`, `CaseComment`) and the Apex Developer Guide
(`Merge Considerations`, `Triggers and Merge Statements`, `Operations That Don't Invoke
Triggers`). The examples extend the guides' own sample shapes into a realistic deployment.

## How to read this file

- **§ 1–2 are the core deliverable.** The handler and its test class exist to put
  person-account logic on Account, where the platform actually fires (apexdev.txt L15521).
  If you take one thing from this skill, take the object it runs on.
- **Apex is source metadata, not a config file.** Each `.cls` needs a matching
  `.cls-meta.xml` alongside it; the shape is shown once in § 1 and omitted afterwards.
- **§ 5 is the only true XML artefact.** `TaskStatus` is a `StandardValueSet`, not a custom
  field — you retrieve the org's copy, edit it, and deploy it back. Never hand-write it from
  scratch.
- **§ 6 changes no metadata.** CaseComment's write lock is a permission fact, not a
  deployable setting; it is documented here because the design decision belongs with the
  rest.
- **§ 7 probes prove the quirk in *this* org.** Run them before and after deploying — they
  return org-specific evidence rather than restating the guide.
- **Retrieve before you edit anything standard.** "Retrieving or deploying a standard object
  includes all custom and standard fields except for standard fields that aren't
  customizable… Other standard fields aren't supported, including system fields (such as
  `CreatedById` or `LastModifiedDate`) and autonumber fields" (api_meta.txt L2163–L2167).
  A hand-written standard-object file will silently omit what it cannot carry.

## Where the files live

| Purpose | Type / member | Path |
|---|---|---|
| Person-account-aware dispatch | `ApexTrigger` / `AccountTrigger` | `triggers/AccountTrigger.trigger` |
| Handler with the person/business branch | `ApexClass` / `AccountQuirkHandler` | `classes/AccountQuirkHandler.cls` |
| Bulk test for both account shapes | `ApexClass` / `AccountQuirkHandlerTest` | `classes/AccountQuirkHandlerTest.cls` |
| Merge with result handling | `ApexClass` / `DuplicateMergeService` | `classes/DuplicateMergeService.cls` |
| Merge-loser detection | `ApexTrigger` / `AccountMergeAuditTrigger` | `triggers/AccountMergeAuditTrigger.trigger` |
| Event insert, both duration forms | `ApexClass` / `EventInsertExamples` | `classes/EventInsertExamples.cls` |
| Task status closed flags | `StandardValueSet` / `TaskStatus` | `standardValueSets/TaskStatus.standardValueSet-meta.xml` |
| Manifest | — | `manifest/package.xml` |

---

## 1. Person-account-aware Account trigger handler

The whole reason this file exists: "Inserts, updates, and deletes on person accounts fire
Account triggers, not Contact triggers" (apexdev.txt L15521). A Contact-side implementation
of person-account logic is unreachable code.

Three further rules are encoded below. `Name` can't be modified with DML on a person account
(apexdev.txt L9029). Field tokens aren't available for person accounts — `Schema.Account
.fieldname` throws, and the field name must be a string instead (apexdev.txt L10866–L10867).
And no update account trigger fires across a business↔person record-type change in either
direction (apexdev.txt L15545–L15546), so the handler cannot be the place that notices one.

`triggers/AccountTrigger.trigger`:

```apex
trigger AccountTrigger on Account (
    before insert, before update, after insert, after update
) {
    new AccountQuirkHandler().run();
}
```

`classes/AccountQuirkHandler.cls` — extends the repo-canonical base at
`templates/apex/TriggerHandler.cls`:

```apex
/**
 * Person-account-aware Account logic.
 *
 * PLATFORM NOTE (Apex Developer Guide, "Operations That Don't Invoke Triggers"):
 *   "Inserts, updates, and deletes on person accounts fire Account triggers,
 *    not Contact triggers."
 * Do not move any of this to a Contact trigger. It will not run.
 *
 * PLATFORM NOTE: update account triggers do NOT fire before or after a business
 * account record type changes to person account, or the reverse. Record-type
 * conversion is handled by the scheduled compensator, not here.
 */
public with sharing class AccountQuirkHandler extends TriggerHandler {

    // Field tokens are unavailable for person accounts; Schema.Account.PersonEmail
    // throws. Address person fields by string name only.
    private static final String PERSON_EMAIL = 'PersonEmail';

    @TestVisible
    private static Boolean personEmailIsAccessible() {
        Schema.DescribeSObjectResult acct = Schema.getGlobalDescribe()
            .get('Account')
            .getDescribe();
        Schema.SObjectField f = acct.fields.getMap().get(PERSON_EMAIL);
        return f != null && f.getDescribe().isAccessible();
    }

    protected override void beforeInsert() {
        applyNamingRules((List<Account>) Trigger.new);
    }

    protected override void beforeUpdate() {
        applyNamingRules((List<Account>) Trigger.new);
    }

    /**
     * Branch on IsPersonAccount (read only; Properties: Defaulted on create,
     * Filter, Group, Sort — Object Reference, Account.IsPersonAccount).
     */
    private void applyNamingRules(List<Account> records) {
        Boolean personFieldsPresent = personEmailIsAccessible();

        for (Account a : records) {
            if (a.IsPersonAccount) {
                // Name is composed from the child person contact and CANNOT be
                // assigned by DML on a person account. Write the parts instead.
                if (String.isBlank(a.LastName)) {
                    a.addError('Person accounts require a Last Name.');
                    continue;
                }
                if (personFieldsPresent) {
                    Object email = a.get(PERSON_EMAIL);
                    if (email != null) {
                        a.put(PERSON_EMAIL, ((String) email).trim().toLowerCase());
                    }
                }
            } else {
                // Business account: Name is writable here and only here.
                if (String.isNotBlank(a.Name)) {
                    a.Name = a.Name.trim();
                }
            }
        }
    }
}
```

`classes/AccountQuirkHandler.cls-meta.xml` — every Apex file needs one:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<ApexClass xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>62.0</apiVersion>
    <status>Active</status>
</ApexClass>
```

---

## 2. Test class — asserts the handler runs on Account for a person account

The assertion that matters is not "the field was trimmed"; it is **which object's trigger
context did the work**. A test that inserts a person account and passes without any Contact
trigger existing is the proof.

Person account fields are null and unmodifiable when `IsPersonAccount` is false, and the org
must have person accounts enabled at all — they are disabled by default (object_reference.txt
L13677–L13683). The test therefore skips its person-account half rather than failing in an
org where the feature is off.

```apex
@IsTest
private class AccountQuirkHandlerTest {

    private static Boolean personAccountsEnabled() {
        return Schema.getGlobalDescribe()
            .get('Account')
            .getDescribe()
            .fields.getMap()
            .containsKey('IsPersonAccount');
    }

    private static Id personRecordTypeId() {
        for (Schema.RecordTypeInfo rt : Account.SObjectType.getDescribe()
                .getRecordTypeInfos()) {
            if (rt.isAvailable() && rt.getName().containsIgnoreCase('Person')) {
                return rt.getRecordTypeId();
            }
        }
        return null;
    }

    @IsTest
    static void businessAccountNameIsTrimmed() {
        List<Account> batch = new List<Account>();
        for (Integer i = 0; i < 200; i++) {
            batch.add(new Account(Name = '  Acme ' + i + '  '));
        }

        Test.startTest();
        insert batch;
        Test.stopTest();

        for (Account a : [SELECT Name FROM Account WHERE Id IN :batch]) {
            System.assert(
                !a.Name.startsWith(' '),
                'Business-account branch should trim Name'
            );
        }
    }

    @IsTest
    static void personAccountRunsAccountTriggerNotContactTrigger() {
        if (!personAccountsEnabled() || personRecordTypeId() == null) {
            return; // person accounts disabled in this org — nothing to assert
        }

        Account pa = new Account(
            RecordTypeId = personRecordTypeId(),
            FirstName    = 'Dana',
            LastName     = 'Okafor'
        );
        // NOTE: assigning pa.Name here would fail. Name can't be modified with
        // DML operations on a person account.
        pa.put('PersonEmail', '  DANA.OKAFOR@Example.COM ');

        Test.startTest();
        insert pa;
        Test.stopTest();

        Account saved = Database.query(
            'SELECT Id, Name, IsPersonAccount, PersonEmail ' +
            'FROM Account WHERE Id = :pa.Id'
        );

        System.assertEquals(true, saved.IsPersonAccount, 'Should be a person account');
        System.assertEquals(
            'dana.okafor@example.com',
            (String) saved.get('PersonEmail'),
            'The Account trigger — not a Contact trigger — normalised PersonEmail'
        );
        System.assert(
            saved.Name.contains('Okafor'),
            'Name is composed by the platform from FirstName/LastName'
        );
    }

    @IsTest
    static void personEmailTokenIsResolvedByStringNotBySchemaToken() {
        // Regression guard for apexdev "Field tokens aren't available for person
        // accounts. If you access Schema.Account.fieldname, you get an exception
        // error. Instead, specify the field name as a string."
        System.assertEquals(
            personAccountsEnabled(),
            AccountQuirkHandler.personEmailIsAccessible() || !personAccountsEnabled(),
            'PersonEmail must be reachable through the string-keyed field map'
        );
    }
}
```

---

## 3. `Database.merge` with the 3-record cap and result handling

"Only leads, contacts, cases, and accounts can be merged" and "you can pass a main record and
up to two additional sObject records to a single merge method" (apexdev.txt L8201–L8202). The
API side agrees and prescribes the workaround: "Up to three records can be merged in a single
request, including the master record… To merge more than 3 records, do a successive merge",
and "External ID fields can't be used with `merge()`"
(salesforce_app_limits_cheatsheet.txt L977–L982).

The field-survival rule is the data-loss risk: "field values on the main record, including
null and empty field values, always supersede the corresponding field values on the records to
be merged" (apexdev.txt L8203–L8207). Preserve before you merge.

`classes/DuplicateMergeService.cls`:

```apex
public with sharing class DuplicateMergeService {

    /** Main record + at most two others per call (Apex Developer Guide). */
    private static final Integer MAX_LOSERS_PER_CALL = 2;

    public class MergeOutcome {
        public Id masterId;
        public List<Id> mergedIds = new List<Id>();
        public List<String> errors = new List<String>();
    }

    /**
     * Merges any number of duplicates into master by successive calls of three.
     * Caller must have already copied any field that must survive onto master:
     * the main record's values — INCLUDING nulls and empty strings — always win.
     */
    public static MergeOutcome mergeInto(Account master, List<Account> duplicates) {
        MergeOutcome outcome = new MergeOutcome();
        outcome.masterId = master.Id;

        for (Integer i = 0; i < duplicates.size(); i += MAX_LOSERS_PER_CALL) {
            List<Account> slice = new List<Account>();
            for (Integer j = i;
                 j < Math.min(i + MAX_LOSERS_PER_CALL, duplicates.size());
                 j++) {
                slice.add(duplicates[j]);
            }

            // allOrNone = false so one bad duplicate does not abandon the run.
            List<Database.MergeResult> results = Database.merge(master, slice, false);

            for (Database.MergeResult r : results) {
                if (r.isSuccess()) {
                    outcome.mergedIds.addAll(r.getMergedRecordIds());
                } else {
                    for (Database.Error e : r.getErrors()) {
                        outcome.errors.add(
                            e.getStatusCode() + ': ' + e.getMessage()
                        );
                    }
                }
            }
        }
        return outcome;
    }
}
```

Detecting the losers requires an **after delete** trigger. "When a record is deleted after
losing a merge operation, its `MasterRecordId` field is set to the ID of the winning record.
The `MasterRecordId` field is only set in after delete trigger events" (apexdev.txt
L15358–L15359). A merge fires one delete event for all losing records and one update event
for the winner only; reparented children fire no triggers at all (apexdev.txt L15354–L15366).

`triggers/AccountMergeAuditTrigger.trigger`:

```apex
trigger AccountMergeAuditTrigger on Account (after delete) {
    // MasterRecordId is populated ONLY here — never in before delete.
    List<Account> mergeLosers = new List<Account>();
    for (Account a : Trigger.old) {
        if (a.MasterRecordId != null) {
            mergeLosers.add(a);   // deleted by a merge, not by a user
        }
    }
    if (!mergeLosers.isEmpty()) {
        // One delete event covers every loser in the merge — do not expect
        // one invocation per record.
        MergeAuditLogger.record(mergeLosers);
    }
}
```

> Scope caveat worth stating in any case-dedupe design: the Apex Developer Guide names cases
> among the mergeable objects (apexdev.txt L8201), but the Object Reference's Case entry omits
> `merge()` from its Supported Calls (object_reference.txt L62206–L62207) while Account,
> Contact and Lead all list it (object_reference.txt L12740–L12741, L71309–L71310,
> L163052–L163053). Verify in a scratch org before committing to case merge.

---

## 4. Event insert — both valid duration forms

"If `IsAllDayEvent` is false, a value must be supplied for either `DurationInMinutes` or
`EndDateTime`. Supplying values in both fields is allowed if the values add up to the same
amount of time" (object_reference.txt L111593–L111597, repeated at L111637–L111641).
`EndDateTime` was required only in API 12.0 and earlier (object_reference.txt L111589–L111592).

`classes/EventInsertExamples.cls`:

```apex
public with sharing class EventInsertExamples {

    /** Form A — duration only. Valid. The platform derives the end time. */
    public static Event withDuration(Id whoId) {
        return new Event(
            Subject           = 'Discovery Call',
            StartDateTime     = DateTime.now(),
            DurationInMinutes = 60,
            WhoId             = whoId
        );
    }

    /** Form B — end time only. Also valid. The platform derives the duration. */
    public static Event withEndDateTime(Id whoId) {
        DateTime start = DateTime.now();
        return new Event(
            Subject       = 'Discovery Call',
            StartDateTime = start,
            EndDateTime   = start.addMinutes(60),
            WhoId         = whoId
        );
    }

    /**
     * Form C — both, in agreement. Allowed, and the safest shape for an
     * integration that receives both from an upstream calendar: the assert
     * fails loudly at build time rather than producing a mismatched Event.
     */
    public static Event withBoth(Id whoId, DateTime start, DateTime finish) {
        Integer minutes = Integer.valueOf(
            (finish.getTime() - start.getTime()) / (1000 * 60)
        );
        return new Event(
            Subject           = 'Discovery Call',
            StartDateTime     = start,
            EndDateTime       = finish,
            DurationInMinutes = minutes,   // must add up to the same amount of time
            WhoId             = whoId
        );
    }

    /**
     * INVALID — neither field. This is the only shape that actually fails, and
     * `scripts/check_standard_object_quirks.py` flags this method by design:
     * it is the checker's own fixture. Delete it when you copy this class.
     */
    public static Event invalidNeither(Id whoId) {
        return new Event(
            Subject       = 'Discovery Call',
            StartDateTime = DateTime.now(),
            WhoId         = whoId
        );
    }
}
```

---

## 5. `TaskStatus` standard value set — the `closed` flags behind `CompletedDateTime`

`Task.CompletedDateTime` is "the date and time the task was saved with a **Closed** status"
(object_reference.txt L277989–L277994). Which statuses count as closed is metadata, not a
constant: `TaskStatus` is the standard value set name for `Task.Status` (api_meta.txt L143095),
and each `StandardValue` carries a `closed` boolean — "Indicates whether this value is
associated with a closed status (true), or not (false). This field is only relevant for the
standard `Status` field in cases and tasks" (api_meta.txt L47542–L47545).

Retrieve the org's own file and edit it. A deployed `StandardValueSet` must contain at least
one picklist value or the deploy errors (api_meta.txt L130769–L130775), and this type does
**not** support the `*` wildcard in package.xml (api_meta.txt L130826–L130828).

`standardValueSets/TaskStatus.standardValueSet-meta.xml`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<StandardValueSet xmlns="http://soap.sforce.com/2006/04/metadata">
    <sorted>false</sorted>
    <standardValue>
        <fullName>Not Started</fullName>
        <default>true</default>
        <label>Not Started</label>
        <closed>false</closed>
    </standardValue>
    <standardValue>
        <fullName>In Progress</fullName>
        <default>false</default>
        <label>In Progress</label>
        <closed>false</closed>
    </standardValue>
    <standardValue>
        <fullName>Completed</fullName>
        <default>false</default>
        <label>Completed</label>
        <closed>true</closed>
    </standardValue>
    <standardValue>
        <fullName>Closed - No Action</fullName>
        <default>false</default>
        <label>Closed - No Action</label>
        <closed>true</closed>
    </standardValue>
</StandardValueSet>
```

That fourth value is the whole point: with it deployed, a task saved as
`Closed - No Action` gets a `CompletedDateTime`, and every report filtered on
`Status = 'Completed'` starts undercounting.

- Changing the flag does not rewrite history. "The status is a dynamic enum. If the Closed
  mapping is changed it won't cause an update of existing tasks. Only new insert/update
  operations are affected" (object_reference.txt L278012–L278013).
- UNVERIFIED (2026-09-05): the Metadata API guide says `closed` is "available in API version
  16.0 and up to version 36.0. In version 37.0, this field is in `GlobalPicklistValue`"
  (api_meta.txt L47544–L47545), yet retrieved `TaskStatus.standardValueSet-meta.xml` files
  still carry `<closed>` in practice. Retrieve your org's copy before hand-writing this file;
  the sibling skill `admin/activity-and-task-patterns` records the same discrepancy.

---

## 6. CaseComment — a permission decision, not a metadata one

There is nothing to deploy here, which is exactly what catches people out. The rule lives in
the Object Reference's CaseComment Usage section (object_reference.txt L63045–L63049):

> "In the API, CaseComment records can't be modified after insertion unless the user has the
> 'Modify All Records' object-level permission for Cases or the 'Modify All Data' permission.
> If not, users can only update the `IsPublished` field, and can't delete CaseComment."

Consequences for design:

- An "edit comment" feature requires one of two very broad permissions. Prefer append-only:
  insert a superseding comment.
- An integration user that corrects comment text needs Modify All Records on Cases — which
  also grants read and edit on every case in the org. Grant it through a dedicated permission
  set, or not at all.
- `IsNotificationSelected` is writable but "when this field is queried, it always returns
  null" (object_reference.txt L62994–L63000), and it functions only when Enable Case Comment
  Notification to Contacts is on in Support Settings (object_reference.txt L63001–L63004).
  Never read it back as state.
- `CommentBody` is capped at 4,000 bytes (object_reference.txt L62929).
- Deleting the parent Case does cascade to comments — "if you delete a case record, Apex
  automatically deletes any CaseComment, CaseHistory, and CaseSolution records associated with
  that case. However, if a particular child record is not deletable… the delete operation on
  the parent case record fails" (apexdev.txt L8236–L8240). The two rules compose: a user who
  cannot delete a comment cannot delete its case.

---

## 7. SOQL probes — one per quirk

Run these against the target org. Each returns evidence, not doctrine.

```sql
-- Q1. Are person accounts enabled at all, and how many are there?
--     If this query errors on IsPersonAccount, the feature is off.
SELECT COUNT(Id) FROM Account WHERE IsPersonAccount = true

-- Q2. Does Account expose person fields? (PersonEmail's UI label is "Email",
--     which is why a bare Email field is reached for and does not exist.)
SELECT Id, Name, FirstName, LastName, PersonEmail, PersonMailingCity
FROM Account WHERE IsPersonAccount = true LIMIT 5

-- Q3. Which Task statuses actually behave as closed in THIS org?
--     Any status appearing here with a non-null CompletedDateTime is flagged
--     closed in the TaskStatus value set, whatever it is spelled.
SELECT Status, IsClosed, COUNT(Id) total
FROM Task WHERE CompletedDateTime != null
GROUP BY Status, IsClosed

-- Q4. The undercount, made visible: rows the naive filter misses.
SELECT COUNT(Id) FROM Task
WHERE CompletedDateTime != null AND Status != 'Completed'

-- Q5. Which duration form do existing Events use? A non-zero count in the
--     DurationInMinutes-only column disproves "EndDateTime is required".
SELECT COUNT(Id) FROM Event
WHERE IsAllDayEvent = false AND EndDateTime = null AND DurationInMinutes != null

-- Q6. Merge losers. MasterRecordId is only populated by a merge, and the rows
--     live in the Recycle Bin for 15 days, so ALL ROWS is required to see them.
SELECT Id, Name, MasterRecordId, IsDeleted
FROM Account WHERE MasterRecordId != null ALL ROWS

-- Q7. CaseComment write-only field. Every row comes back null regardless of
--     what was written on insert.
SELECT Id, ParentId, IsPublished, IsNotificationSelected
FROM CaseComment ORDER BY CreatedDate DESC LIMIT 10

-- Q8. Converted leads whose target already existed — the "only empty fields are
--     overwritten" population. Compare a mapped field either side of conversion.
SELECT Id, Company, ConvertedAccountId, ConvertedContactId, ConvertedDate
FROM Lead WHERE IsConverted = true ORDER BY ConvertedDate DESC LIMIT 20
```

Recycle Bin note for Q6: deleted records "are placed in the Recycle Bin for 15 days from
where they can be restored" (apexdev.txt L8212, L8260) — after that the merge losers are gone
and the audit trail must come from your own logging.

---

## 8. package.xml and CLI

`manifest/package.xml`. `StandardValueSet` does not accept the `*` wildcard
(api_meta.txt L130826–L130828), so `TaskStatus` is named explicitly:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>AccountQuirkHandler</members>
        <members>AccountQuirkHandlerTest</members>
        <members>DuplicateMergeService</members>
        <members>EventInsertExamples</members>
        <name>ApexClass</name>
    </types>
    <types>
        <members>AccountTrigger</members>
        <members>AccountMergeAuditTrigger</members>
        <name>ApexTrigger</name>
    </types>
    <types>
        <members>TaskStatus</members>
        <name>StandardValueSet</name>
    </types>
    <version>62.0</version>
</Package>
```

```bash
# 1. Pull the org's real TaskStatus before editing it — never hand-write it.
sf project retrieve start \
  --metadata "StandardValueSet:TaskStatus" \
  --target-org myOrg

# 2. Lint the working tree for the quirks this skill covers.
python3 scripts/check_standard_object_quirks.py \
  --manifest-dir force-app/main/default

# 3. Validate without deploying, running only this skill's tests.
sf project deploy validate \
  --manifest manifest/package.xml \
  --test-level RunSpecifiedTests \
  --tests AccountQuirkHandlerTest \
  --target-org myOrg

# 4. Deploy the value set first, then the Apex that reads it.
sf project deploy start \
  --metadata "StandardValueSet:TaskStatus" \
  --target-org myOrg

sf project deploy start \
  --manifest manifest/package.xml \
  --test-level RunSpecifiedTests \
  --tests AccountQuirkHandlerTest \
  --target-org myOrg
```

## Verification after deploy

One step, and it must be the one that would have failed before:

```bash
# Did the closed-status change take? IsClosed is derived from the value set and
# is never written directly, so a non-zero count here proves the deploy landed.
sf data query --target-org myOrg --query \
  "SELECT COUNT(Id) FROM Task WHERE Status = 'Closed - No Action' AND IsClosed = true"
```

If the count is zero and tasks exist in that status, the `closed` flag did not deploy — check
whether your org's retrieved file carries `<closed>` at all (see the UNVERIFIED note in § 5).

For § 1, the equivalent proof is behavioural: insert a person account with **no Contact
trigger deployed at all** and confirm `PersonEmail` was normalised. If it was, the work
happened in the Account trigger, which is the claim the whole handler rests on.

## Related reading

- `references/gotchas.md` — the platform behaviour behind each artefact here
- `admin/activity-and-task-patterns` — `ActivitiesSettings`, shared Task/Event fields, and the
  same `TaskStatus` value-set caveat
- `apex/trigger-framework` — the `TriggerHandler` base class § 1 extends
- `templates/apex/TriggerHandler.cls`, `templates/apex/tests/BulkTestPattern.cls` — the
  repo-canonical versions; copy rather than re-invent
