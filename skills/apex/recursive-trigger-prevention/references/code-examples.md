# Code Examples — Recursive Trigger Prevention

A complete, deployable recursion-guard implementation built **on top of** the canonical trigger
framework, not beside it. Read `templates/apex/TriggerHandler.cls` and
`templates/apex/TriggerControl.cls` before you copy anything here — this package subclasses the first
and consumes the second. It does not replace either.

## What this builds

| File | Type | Role |
|---|---|---|
| `RecursionGuard.cls` | class | Per-record-Id processed set, scoped by `Trigger.operationType`, with a watched-field fingerprint so a *genuine* second change re-enters |
| `AccountTriggerHandler.cls` | class | `extends TriggerHandler`; overrides `afterUpdate()`; rolls a value down to Contacts and is the loop breaker for the Apex↔Flow ping-pong |
| `AccountTrigger.trigger` | trigger | One line. Dispatch only. |
| `AccountRecursionGuardTest.cls` | test | 400-record chunking proof, invocation counter, cross-record re-entry, bypass path |
| `Health_Score__c`, `Account_Health_Score__c` | fields | The two fields the loop ping-pongs between |
| `package.xml` | manifest | Deploy set |

## Prerequisites (deploy these first, from `templates/apex/`)

1. `templates/apex/cmdt/Trigger_Setting__mdt/` — the whole folder. `TriggerControl.cls` does not
   compile without its three fields.
2. `templates/apex/TriggerControl.cls` (+ `-meta.xml`).
3. `templates/apex/TriggerHandler.cls` (+ `-meta.xml`).
4. A `TriggerControl_BypassAll` Custom Permission. Not shipped — `templates/apex/README.md` has the
   metadata. `TriggerControl.hasBypassAllPermission()` fails closed when it is absent, so the org still
   works; the migration bypass simply does nothing until you create it.

---

## 1. `RecursionGuard.cls`

The guard is a `Map<String, Map<Id, String>>` keyed by operation type, not a `Boolean`. Two properties
make it survive the failure modes a `hasRun` flag does not:

- The key is `(operationType, recordId)`. A static `Boolean` is one bit for the whole transaction, and
  a static variable "persists within the context of a single transaction" across every trigger
  invocation in it (`apexdev` L3738–3740) — so record 201 in chunk two sees the flag already true.
- The value is a **fingerprint** of the fields this handler cares about. A workflow field update
  re-fires before-update and after-update triggers "one more time (and only one more time)"
  (`apexdev` L15455–15460); that pass carries *different* field values and is often work you still want
  done. Comparing the fingerprint lets that pass through while a byte-identical self-DML echo is
  suppressed.

```apex
/**
 * RecursionGuard — per-record, per-operation re-entry control for trigger handlers.
 *
 * Consumed by handlers that extend templates/apex/TriggerHandler.cls. It does NOT replace
 * TriggerHandler's own depth counter (that is a circuit breaker for runaway loops) or
 * TriggerControl (that is the declarative on/off switch). This is the third, finest layer:
 * "have I already done THIS work for THIS record in THIS transaction with THESE values?"
 *
 * Why not a static Boolean: a static variable is static within the scope of the Apex
 * transaction and persists across every trigger invocation in it (Apex Developer Guide,
 * "Using Static Methods and Variables"). One Boolean therefore silences records 201-400 of a
 * 400-record DML, because the platform invokes the trigger once per batch and Trigger.size
 * "includes only the number of records in the current batch".
 */
public with sharing class RecursionGuard {

    @TestVisible
    private static Map<String, Map<Id, String>> fingerprintsByContext =
        new Map<String, Map<Id, String>>();

    /**
     * True when this record has already been processed in this transaction, for this
     * operation type, with an identical fingerprint of the watched fields.
     */
    public static Boolean isProcessed(String context, Id recordId, String fingerprint) {
        Map<Id, String> seen = fingerprintsByContext.get(context);
        if (seen == null) {
            return false;
        }
        String previous = seen.get(recordId);
        return previous != null && previous == fingerprint;
    }

    public static void markProcessed(String context, Id recordId, String fingerprint) {
        Map<Id, String> seen = fingerprintsByContext.get(context);
        if (seen == null) {
            seen = new Map<Id, String>();
            fingerprintsByContext.put(context, seen);
        }
        seen.put(recordId, fingerprint);
    }

    /**
     * Context key. Trigger.operationType returns a System.TriggerOperation enum
     * (BEFORE_INSERT, BEFORE_UPDATE, BEFORE_DELETE, AFTER_INSERT, AFTER_UPDATE,
     * AFTER_DELETE, AFTER_UNDELETE) — Apex Developer Guide, Trigger Context Variables.
     * Scoping by it stops a before-update guard from silencing after-update work.
     */
    public static String contextKey(String handlerName) {
        String op = Trigger.operationType == null
            ? 'NO_TRIGGER_CONTEXT'
            : String.valueOf(Trigger.operationType);
        return handlerName + '.' + op;
    }

    /**
     * Test hook. Statics are reinitialised at the start of every test METHOD, but not
     * between the multiple DML statements inside one test method, and not between the
     * retry attempts of a partial-success DML. Call this when a single test method needs
     * two independent transactions-worth of guard state.
     */
    @TestVisible
    public static void reset() {
        fingerprintsByContext = new Map<String, Map<Id, String>>();
    }
}
```

`RecursionGuard.cls-meta.xml` — the same file shape applies to every class below.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<ApexClass xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>67.0</apiVersion>
    <status>Active</status>
</ApexClass>
```

API version 67.0 is Summer '26 (`apexdev` L2). At 67.0 a class with no sharing declaration runs in
`with sharing` mode (`apexdev` L4961–4963); the explicit `with sharing` above is kept so the intent
survives a later downgrade of the class's API version.

---

## 2. `AccountTriggerHandler.cls`

This is a **consumer** of `templates/apex/TriggerHandler.cls`. It overrides one virtual method; it does
not re-implement dispatch, depth counting, or the `TriggerControl` check — `TriggerHandler.run()`
already does all three before `afterUpdate()` is reached.

```apex
/**
 * AccountTriggerHandler — rolls Account.Health_Score__c down to its Contacts.
 *
 * The loop this breaks (Apex <-> Flow ping-pong):
 *   1. Account.Health_Score__c changes -> this handler updates Contact.Account_Health_Score__c
 *   2. an after-save record-triggered flow on Contact writes a summary back to the Account
 *   3. that write re-enters this handler -> step 1
 *
 * Step 2 is real: "When a process or flow executes a DML operation, the affected record goes
 * through the save procedure" (Apex Developer Guide, Triggers and Order of Execution, step 13).
 * Nothing in the platform stops the cycle before the stack-depth ceiling of 16
 * (Execution Governors and Limits: "Total stack depth for any Apex invocation that recursively
 * fires triggers due to insert, update, or delete statements" = 16; apexdev L19559), and hitting
 * that ceiling raises a LimitException, which the guide lists among the "uncatchable Apex
 * exceptions ... caused by reaching governor limits" (apexdev L17856) -- not a graceful no-op.
 *
 * The break is the fingerprint check below, NOT TriggerHandler.skipOnce(). skipOnce sets one
 * flag and the first invocation consumes it; a DML of more than 200 records is invoked once per
 * batch, so batches two onward run unguarded. skipOnce is safe only for a DML you can prove is
 * <= 200 rows.
 */
public with sharing class AccountTriggerHandler extends TriggerHandler {

    private static final String HANDLER = 'AccountTriggerHandler';

    /** Test-only invocation counter. Proves how many times the platform entered this method. */
    @TestVisible
    private static Integer afterUpdateInvocations = 0;

    /** Test-only tally of how many distinct Account Ids actually did work. */
    @TestVisible
    private static Set<Id> processedAccountIds = new Set<Id>();

    protected override void afterUpdate() {
        afterUpdateInvocations++;

        Map<Id, Account> oldMap = (Map<Id, Account>) Trigger.oldMap;
        String context = RecursionGuard.contextKey(HANDLER);

        List<Account> toRollDown = new List<Account>();
        for (Account acct : (List<Account>) Trigger.new) {
            String fingerprint = fingerprintOf(acct);

            // 1. Delta gate. Nothing to roll down when the watched field did not move.
            Account priorVersion = oldMap.get(acct.Id);
            if (priorVersion != null && priorVersion.Health_Score__c == acct.Health_Score__c) {
                continue;
            }

            // 2. Re-entry gate. Same record, same operation, same watched values as a pass we
            //    already served in this transaction => this is the echo of our own DML.
            if (RecursionGuard.isProcessed(context, acct.Id, fingerprint)) {
                continue;
            }

            RecursionGuard.markProcessed(context, acct.Id, fingerprint);
            processedAccountIds.add(acct.Id);
            toRollDown.add(acct);
        }

        if (toRollDown.isEmpty()) {
            return;
        }
        rollDownToContacts(toRollDown);
    }

    /**
     * The watched-field fingerprint. Keep it to the fields this handler reads, so that an
     * unrelated update from another automation in the same transaction is not mistaken for
     * a re-entry that must be served.
     */
    private String fingerprintOf(Account acct) {
        return String.valueOf(acct.Health_Score__c) + '|' + String.valueOf(acct.OwnerId);
    }

    private void rollDownToContacts(List<Account> accounts) {
        Map<Id, Account> byId = new Map<Id, Account>(accounts);

        List<Contact> updates = new List<Contact>();
        for (Contact con : [
            SELECT Id, AccountId, Account_Health_Score__c
            FROM Contact
            WHERE AccountId IN :byId.keySet()
        ]) {
            Decimal target = byId.get(con.AccountId).Health_Score__c;
            if (con.Account_Health_Score__c == target) {
                continue;
            }
            updates.add(new Contact(Id = con.Id, Account_Health_Score__c = target));
        }

        if (updates.isEmpty()) {
            return;
        }
        update updates;
    }

    @TestVisible
    private static void resetCounters() {
        afterUpdateInvocations = 0;
        processedAccountIds = new Set<Id>();
    }
}
```

### How to read it

- **Two gates, in this order.** The delta check runs first because it is free and removes the common
  case. The guard check runs second because it costs a map lookup and only matters once the field
  genuinely moved.
- **`Trigger.oldMap` is cast, not queried.** `oldMap` is available in update and delete triggers
  (`apexdev` L15019–15020). One caveat lives in the fingerprint: after a workflow field update re-fires
  the update triggers, `Trigger.old` still holds the values from *before the initial user update*, not
  the workflow-updated ones (`apexdev` L15494–15498). The delta gate therefore compares
  original-vs-workflow-updated on that pass, which is what you want — it sees a change and lets it
  through.
- **No `try/finally` reset.** The guard is a transaction-scoped static; there is no state to restore.
- **The DML is unconditional at the end.** `update updates;` is all-or-none. If you switch it to
  `Database.update(updates, false)`, read the partial-success gotcha in `references/gotchas.md` first —
  the retry attempts refire triggers with the statics *not* reset.

---

## 3. `AccountTrigger.trigger`

```apex
trigger AccountTrigger on Account (
    before insert, before update, before delete,
    after insert, after update, after delete, after undelete
) {
    new AccountTriggerHandler().run();
}
```

`AccountTrigger.trigger-meta.xml`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<ApexTrigger xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>67.0</apiVersion>
    <status>Active</status>
</ApexTrigger>
```

One trigger per object is not style preference here — "If more than one trigger is defined on an object
for the same event, the order of trigger execution isn't guaranteed" (`apexdev` L15502–15504). Two
triggers on Account means the guard in one of them may or may not have been set when the other runs,
and the answer can change between deployments.

---

## 4. The data-load bypass (`TriggerControl`)

A migration does not want a smarter guard; it wants the handler off. `TriggerControl` already provides
two switches — use them rather than adding a third static to the handler.

**Switch A — per-handler, deployable.** A `Trigger_Setting__mdt` record. Deactivate for the load, flip
it back after. `TriggerControl.isActive()` returns the record's `Is_Active__c`, defaulting to `true`
when no record exists.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CustomMetadata xmlns="http://soap.sforce.com/2006/04/metadata"
                xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <label>Account AccountTriggerHandler</label>
    <protected>false</protected>
    <values>
        <field>Object_API_Name__c</field>
        <value xsi:type="xsd:string">Account</value>
    </values>
    <values>
        <field>Handler_Class__c</field>
        <value xsi:type="xsd:string">AccountTriggerHandler</value>
    </values>
    <values>
        <field>Is_Active__c</field>
        <value xsi:type="xsd:boolean">true</value>
    </values>
</CustomMetadata>
```

File name: `force-app/main/default/customMetadata/Trigger_Setting.Account_AccountTriggerHandler.md-meta.xml`.

**Switch B — per-user, instant.** Assign the `TriggerControl_BypassAll` Custom Permission to the
integration/migration user through a permission set. Every handler that runs `TriggerHandler.run()`
returns before dispatch for that user only; ordinary users keep their automation. This is the switch to
use for a Data Loader run, because it needs no deployment and cannot be forgotten in a way that affects
anyone else.

Deeper treatment of both switches — audit trail, re-enable checklists, hierarchy custom settings as a
third option — belongs to `apex/apex-trigger-bypass-and-killswitch-patterns`. This skill only asserts
that the bypass is where a data load belongs, and that a bypass is *not* a recursion guard: it stops the
work, the guard shapes it.

---

## 5. `AccountRecursionGuardTest.cls`

```apex
@IsTest
private class AccountRecursionGuardTest {

    private static final Integer BULK_SIZE = 400;

    @TestSetup
    static void makeData() {
        List<Account> accounts = new List<Account>();
        for (Integer i = 0; i < BULK_SIZE; i++) {
            accounts.add(new Account(Name = 'Guard Co ' + i, Health_Score__c = 10));
        }
        insert accounts;

        List<Contact> contacts = new List<Contact>();
        for (Account acct : accounts) {
            contacts.add(new Contact(
                LastName = 'Child of ' + acct.Name,
                AccountId = acct.Id,
                Account_Health_Score__c = 10
            ));
        }
        insert contacts;
    }

    /**
     * The chunking proof. 400 records in one update statement. "DML operations that include
     * over 200 records are processed in batches, and the trigger is invoked for each batch"
     * (Apex Developer Guide, Trigger Context Variables, Trigger.size). A static Boolean guard
     * would be consumed by batch one and would silence all 200 records of batch two.
     */
    @IsTest
    static void guardSurvivesTwoHundredRecordChunking() {
        AccountTriggerHandler.resetCounters();
        RecursionGuard.reset();

        List<Account> accounts = [SELECT Id, Health_Score__c FROM Account ORDER BY Name];
        Assert.areEqual(BULK_SIZE, accounts.size(), 'test setup did not create 400 Accounts');
        for (Account acct : accounts) {
            acct.Health_Score__c = 55;
        }

        Test.startTest();
        update accounts;
        Test.stopTest();

        Assert.isTrue(
            AccountTriggerHandler.afterUpdateInvocations >= 2,
            'expected the platform to invoke afterUpdate once per batch of 200; got '
                + AccountTriggerHandler.afterUpdateInvocations
        );
        Assert.areEqual(
            BULK_SIZE,
            AccountTriggerHandler.processedAccountIds.size(),
            'every one of the 400 Accounts must pass the guard exactly once — a static Boolean '
                + 'guard scores 200 here'
        );

        Integer rolledDown = [
            SELECT COUNT() FROM Contact WHERE Account_Health_Score__c = 55
        ];
        Assert.areEqual(BULK_SIZE, rolledDown, 'the roll-down skipped records the guard let through');
    }

    /**
     * The re-entry proof. Re-running the same update inside the SAME test method reuses the
     * same static guard state, which is exactly what the second pass of a real transaction
     * looks like. Identical values must be suppressed; a genuinely new value must not be.
     */
    @IsTest
    static void identicalSecondPassSuppressedNewValueAllowed() {
        AccountTriggerHandler.resetCounters();
        RecursionGuard.reset();

        List<Account> accounts = [SELECT Id, Health_Score__c FROM Account LIMIT 5];
        for (Account acct : accounts) {
            acct.Health_Score__c = 71;
        }
        update accounts;
        Integer afterFirstPass = AccountTriggerHandler.processedAccountIds.size();

        // Same values again: the delta gate stops it before the guard is even consulted.
        update accounts;
        Assert.areEqual(
            afterFirstPass,
            AccountTriggerHandler.processedAccountIds.size(),
            'an unchanged re-save must not be treated as new work'
        );

        // A genuinely new value: the fingerprint differs, so this pass must be served.
        for (Account acct : accounts) {
            acct.Health_Score__c = 72;
        }
        update accounts;
        Assert.areEqual(
            5,
            [SELECT COUNT() FROM Contact WHERE Account_Health_Score__c = 72],
            'a real second change was swallowed by the guard — the guard is too broad'
        );
    }

    /**
     * The cross-record proof. Updating Account A must not silence Account B in the same
     * transaction. This is the single behaviour a static Boolean guard cannot express.
     */
    @IsTest
    static void guardIsPerRecordNotPerTransaction() {
        AccountTriggerHandler.resetCounters();
        RecursionGuard.reset();

        List<Account> two = [SELECT Id, Health_Score__c FROM Account LIMIT 2];
        two[0].Health_Score__c = 91;
        two[1].Health_Score__c = 92;

        Test.startTest();
        update two;
        Test.stopTest();

        Assert.areEqual(
            2,
            AccountTriggerHandler.processedAccountIds.size(),
            'both Accounts in one DML must be processed'
        );
    }

    /**
     * The bypass proof. With the handler switched off in TriggerControl, TriggerHandler.run()
     * returns before dispatch and afterUpdate() is never entered.
     */
    @IsTest
    static void triggerControlBypassStopsTheHandlerEntirely() {
        AccountTriggerHandler.resetCounters();
        RecursionGuard.reset();
        TriggerControl.overrideForTest('Account', 'AccountTriggerHandler', false);

        List<Account> accounts = [SELECT Id, Health_Score__c FROM Account LIMIT 10];
        for (Account acct : accounts) {
            acct.Health_Score__c = 33;
        }

        Test.startTest();
        update accounts;
        Test.stopTest();

        Assert.areEqual(
            0,
            AccountTriggerHandler.afterUpdateInvocations,
            'the bypass did not stop dispatch'
        );
        Assert.areEqual(
            0,
            [SELECT COUNT() FROM Contact WHERE Account_Health_Score__c = 33],
            'the handler still wrote Contacts while bypassed'
        );
    }

    /**
     * The guard itself, unit-tested away from any trigger. Trigger.operationType is null
     * outside trigger context, so contextKey() must still produce a stable key.
     */
    @IsTest
    static void guardKeysByContextAndFingerprint() {
        RecursionGuard.reset();
        Id fakeId = [SELECT Id FROM Account LIMIT 1].Id;

        String keyA = RecursionGuard.contextKey('H');
        Assert.isTrue(keyA.endsWith('NO_TRIGGER_CONTEXT'), 'contextKey must tolerate null operationType');

        Assert.isFalse(RecursionGuard.isProcessed(keyA, fakeId, 'v1'), 'nothing processed yet');
        RecursionGuard.markProcessed(keyA, fakeId, 'v1');
        Assert.isTrue(RecursionGuard.isProcessed(keyA, fakeId, 'v1'), 'same fingerprint must be suppressed');
        Assert.isFalse(RecursionGuard.isProcessed(keyA, fakeId, 'v2'), 'a new fingerprint must be allowed through');
        Assert.isFalse(RecursionGuard.isProcessed('OtherContext', fakeId, 'v1'), 'contexts must not bleed');
    }
}
```

### The workflow field-update re-fire test: you cannot write it self-contained

There is no Apex API that creates a workflow rule, and a test class cannot assert on a re-fire that only
happens when a `WorkflowFieldUpdate` exists in the target org. The behaviour is real and documented — a
workflow field update runs before-update and after-update triggers "one more time (and only one more
time)" regardless of whether the original operation was an insert or an update (`apexdev` L15455–15460)
— but proving it needs org metadata that the test cannot provision.

Two honest substitutes, in preference order:

1. **Deploy the workflow rule to a scratch org and count in the debug log** (section 7 below). This is
   the only way to observe the third invocation.
2. **Assert the shape instead of the event.** `identicalSecondPassSuppressedNewValueAllowed` above
   drives a second pass with changed values through the same static state, which is what the re-fire
   presents to the handler. It proves the guard's decision is right; it does not prove the platform
   re-fired.

Do not write a test that calls `afterUpdate()` directly to "simulate" the re-fire. Outside trigger
context `Trigger.new` is null and `TriggerHandler.run()` returns immediately
(`!Trigger.isExecuting && !Test.isRunningTest()`), so the test would be asserting on a code path the
platform never takes.

---

## 6. Fields and `package.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CustomField xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>Health_Score__c</fullName>
    <label>Health Score</label>
    <type>Number</type>
    <precision>5</precision>
    <scale>0</scale>
    <required>false</required>
    <trackHistory>false</trackHistory>
</CustomField>
```

`Contact.Account_Health_Score__c` is the same definition with `<fullName>Account_Health_Score__c</fullName>`
and `<label>Account Health Score</label>`.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>Account.Health_Score__c</members>
        <members>Contact.Account_Health_Score__c</members>
        <name>CustomField</name>
    </types>
    <types>
        <members>Trigger_Setting__mdt</members>
        <name>CustomObject</name>
    </types>
    <types>
        <members>Trigger_Setting.Account_AccountTriggerHandler</members>
        <name>CustomMetadata</name>
    </types>
    <types>
        <members>TriggerControl_BypassAll</members>
        <name>CustomPermission</name>
    </types>
    <types>
        <members>TriggerControl</members>
        <members>TriggerHandler</members>
        <members>RecursionGuard</members>
        <members>AccountTriggerHandler</members>
        <members>AccountRecursionGuardTest</members>
        <name>ApexClass</name>
    </types>
    <types>
        <members>AccountTrigger</members>
        <name>ApexTrigger</name>
    </types>
    <version>67.0</version>
</Package>
```

## 7. Deploy order and verification

Deploy in three passes. Passes 1 and 2 exist because `TriggerControl` reads
`Trigger_Setting__mdt` fields in SOQL and will not compile before they exist.

UNVERIFIED (2026-09-05): the `sf` CLI invocations in this section — `sf project deploy start`,
`sf apex run test`, `sf apex tail log` and their flags — are Salesforce CLI syntax, which is not
defined in the Apex Developer Guide or the Metadata API Guide and could not be checked against an
official source in this environment. The deploy *order* and the three-pass dependency reasoning
are grounded in `templates/apex/README.md`; only the command spellings are unverified. Confirm
with `sf project deploy start --help` before scripting them.

```bash
# Pass 1 — declarative dependencies
sf project deploy start \
  --source-dir force-app/main/default/objects \
  --source-dir force-app/main/default/customPermissions \
  --target-org myOrg

# Pass 2 — framework classes (from templates/apex/)
sf project deploy start \
  --metadata ApexClass:TriggerControl \
  --metadata ApexClass:TriggerHandler \
  --target-org myOrg

# Pass 3 — this skill's classes, the trigger, and the CMDT record
sf project deploy start --manifest manifest/package.xml --target-org myOrg
```

**Verification 1 — the tests.**

```bash
sf apex run test \
  --class-names AccountRecursionGuardTest \
  --result-format human --code-coverage --wait 20 --target-org myOrg
```

`guardSurvivesTwoHundredRecordChunking` failing with 200 rather than 400 processed Ids means a
transaction-wide guard has crept back in.

**Verification 2 — count the invocations in a real debug log.** This is how you observe the workflow
re-fire and any Flow ping-pong that the test cannot reach. `CODE_UNIT_STARTED` and `CODE_UNIT_FINISHED`
delimit units of code, and a trigger is one unit (`apexdev` L38178–38190); the log line carries the
event name, e.g. `CODE_UNIT_STARTED|[EXTERNAL]MyTrigger on Account trigger event BeforeInsert for [new]`.

```bash
sf apex tail log --target-org myOrg --color > /tmp/save.log
# ... perform one Account edit in the UI, then Ctrl-C ...
grep -c 'CODE_UNIT_STARTED.*AccountTrigger on Account trigger event AfterUpdate' /tmp/save.log
```

Read the count like this:

| Count for one user edit | Meaning |
|---:|---|
| 1 | No re-entry. The save order ran once. |
| 2 | One re-fire. Expected when a workflow field update or an after-save flow writes back to the record. |
| 3+ | A loop. Trace which automation issued the write; the ceiling is a stack depth of 16 (`apexdev` L19559), reached as an uncatchable limit exception on the user's save. |

**Verification 3 — confirm the roll-down actually happened.** A guard that is too broad shows up as
silence, not as an error, so assert on the data.

```sql
SELECT Account.Health_Score__c, Account_Health_Score__c, COUNT(Id)
FROM Contact
WHERE Account.Health_Score__c != null
GROUP BY Account.Health_Score__c, Account_Health_Score__c
```

Any row where the two columns disagree is a Contact the guard skipped.

## Related reading

- `templates/apex/TriggerHandler.cls` — dispatch, depth ceiling, `skipOnce`
- `templates/apex/TriggerControl.cls` — CMDT + Custom Permission switch
- `templates/apex/tests/BulkTestPattern.cls` — the 200-record bulk test shape reused above
- `references/gotchas.md` — the platform behaviours each gate above is defending against
