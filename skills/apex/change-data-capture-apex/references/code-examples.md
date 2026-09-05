# Code Examples — Change Data Capture Apex

One complete, deployable CDC subscriber slice for `Account`: the metadata that turns CDC on,
the trigger, an idempotent handler, the dedupe store, the subscriber config, the test class,
`package.xml`, deploy order, and verification.

Canonical building blocks are referenced by path, not copied:

| Template | Used for |
|---|---|
| `templates/apex/ApplicationLogger.cls` | every log line in the handler (`ApplicationLogger.warn/error/flush`) |
| `templates/apex/custom_objects/Application_Log__c.object-meta.xml` | the object `ApplicationLogger` writes to — deploy it with this slice |
| `templates/apex/TriggerHandler.cls` | the trigger-plus-handler shape. A change event trigger only ever reaches `afterInsert()`, so the CDC routing lives on `changeType` inside the handler, not in `TriggerHandler`'s dispatch |
| `templates/apex/tests/TestDataFactory.cls` | `Account` fixtures in the test class |
| `templates/apex/BaseSelector.cls` | where the "re-hydrate the current record state" query belongs once this grows past one object |

Header field names, `changeType` values, the `recordIds` merge rule and the wildcard case are all from
the `EventBus.ChangeEventHeader` reference (`apexrefguide` L157167–157447). Everything the Apex and
Metadata API guides do **not** state carries an UNVERIFIED marker beside it.

---

## Artifact 1 — turn CDC on for the object as deployable metadata

Selecting an entity on the **Change Data Capture** page in Setup is the same thing as a
`PlatformEventChannelMember` on the standard `ChangeEvents` channel (`api_meta` L95842–95844,
L96098–96108). Ship it with the trigger instead of asking someone to click Setup in every org.

File: `force-app/main/default/platformEventChannelMembers/ChangeEvents_AccountChangeEvent.platformEventChannelMember-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<PlatformEventChannelMember xmlns="http://soap.sforce.com/2006/04/metadata">
    <eventChannel>ChangeEvents</eventChannel>
    <selectedEntity>AccountChangeEvent</selectedEntity>
</PlatformEventChannelMember>
```

**How to read it:**

- `eventChannel` is `ChangeEvents` for the standard channel; a custom channel is `MyChannel__chn` (`api_meta` L96051–96055).
- `selectedEntity` is the change event name: `AccountChangeEvent` for a standard object, `MyObject__ChangeEvent` for a custom one (`api_meta` L96069–96072).
- The file name without the extension **is** the component full name, and the format is `ChannelName_EventName` (`api_meta` L96105–96108). Get this wrong and the deploy fails on a name that looks right.
- The standard `ChangeEvents` channel itself cannot be deployed or retrieved in API 47.0 and later — only its members (`api_meta` L95921). Do not try to add a `PlatformEventChannel` file for `ChangeEvents`.
- `createMetadata()` and `deleteMetadata()` are not supported for this type (`api_meta` L96090–96091); deploy and `destructiveChanges.xml` are the only ways in and out.
- Requires **Customize Application** to deploy or retrieve (`api_meta` L96040–96041).

## Artifact 2 — a custom channel with enriched fields and a filter (optional)

Use this instead of Artifact 1 when the subscriber needs fields that did not change on every event,
or needs the platform to drop events it does not care about before they reach Apex.

File: `force-app/main/default/platformEventChannels/SalesEvents__chn.platformEventChannel-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<PlatformEventChannel xmlns="http://soap.sforce.com/2006/04/metadata">
    <channelType>data</channelType>
    <label>Sales Events</label>
</PlatformEventChannel>
```

File: `force-app/main/default/platformEventChannelMembers/SalesEvents_chn_AccountChangeEvent.platformEventChannelMember-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<PlatformEventChannelMember xmlns="http://soap.sforce.com/2006/04/metadata">
    <enrichedFields>
        <name>AccountNumber</name>
    </enrichedFields>
    <enrichedFields>
        <name>OwnerId</name>
    </enrichedFields>
    <eventChannel>SalesEvents__chn</eventChannel>
    <filterExpression><![CDATA[(BillingCountry='US')]]></filterExpression>
    <selectedEntity>AccountChangeEvent</selectedEntity>
</PlatformEventChannelMember>
```

**How to read it:**

- `channelType` is `data` for change events and `event` for platform events (`api_meta` L95879–95883). A channel holds one kind only.
- `enrichedFields` — "A non-empty enriched field is added to an update or delete change event even when not changed", API 51.0 and later (`api_meta` L96047–96050). This is the supported way to get a stable business key (an external id, an account number) onto every event without a SOQL round trip.
  - UNVERIFIED (2026-09-05): `api_meta` L96048–96050 documents enrichment by pointing at "Enrich Change Events with Extra Fields When Subscribed with CometD" in the Change Data Capture Developer Guide. Whether enriched fields are also populated on the event object seen by an **Apex** change event trigger is not stated in the Metadata API guide, the Apex Developer Guide or the Apex Reference Guide. Confirm in a sandbox before designing a handler that depends on an enriched field being non-null.
- `filterExpression` is SOQL-shaped, API 56.0 and later (`api_meta` L96057–96066). Wrap it in `CDATA` so `<` and `&` in a comparison do not break the XML.
- **The double-underscore trap:** the *channel* is `SalesEvents__chn`, but the channel *member's* full name collapses it to one underscore — `SalesEvents_chn_AccountChangeEvent`, not `SalesEvents__chn_AccountChangeEvent` (`api_meta` L96153–96157). A custom object member is `SalesEvents_chn_MyCustomObj_ChangeEvent` (`api_meta` L96181).

## Artifact 3 — the trigger (`AccountChangeEventTrigger.trigger`)

```apex
/**
 * Subscriber for Account change events.
 *
 * `after insert` is the only context a change event trigger has: the event is published after the
 * originating transaction committed, so there is nothing to intercept before it. See the Apex
 * Developer Guide's change event trigger sample, apexdev L29634.
 *
 * The trigger body is one line on purpose — it stays testable and the batch (up to 2,000 events,
 * apexdev L19862) is handled in one place.
 */
trigger AccountChangeEventTrigger on AccountChangeEvent (after insert) {
    AccountChangeEventHandler.handle(Trigger.new);
}
```

File: `AccountChangeEventTrigger.trigger-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<ApexTrigger xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>66.0</apiVersion>
    <status>Active</status>
</ApexTrigger>
```

`66.0` is deliberate, not stale. In **API version 67.0 and later Apex runs in user context by default**
and classes with no sharing declaration run `with sharing` (`apexdev` L11744–11746). The subscriber's
running user is the Automated Process entity, and "Automated Process users can't perform Object and
FLS checks in custom code unless appropriate permission sets are explicitly applied to those users"
(`apexdev` L11921–11922). Moving this slice to 67.0 is a security-context change, not a version bump —
either grant the Automated Process user the object and field permissions first, or set a real running
user in Artifact 6.

## Artifact 4 — the handler (`AccountChangeEventHandler.cls`)

```apex
/**
 * Idempotent Account change event subscriber.
 *
 * Contract this handler holds to:
 *   1. One event can carry MANY record ids (apexrefguide L157393-157397) and, for a field type
 *      conversion that loses data, a wildcard like '001*' instead of an id (apexrefguide L157413-157417).
 *   2. Redelivery is possible, so the unit of work is keyed on transactionKey + sequenceNumber:
 *      one transaction produces several numbered events (a lead conversion produces four —
 *      apexrefguide L157429-157436), so transactionKey alone is not unique.
 *   3. GAP_* and GAP_OVERFLOW events are a resync signal, not a data payload.
 *   4. No SOQL or DML inside the event loop. The batch is up to 2,000 (apexdev L19862) against
 *      100 SOQL / 150 DML (apexdev L19542, L19553).
 */
public with sharing class AccountChangeEventHandler {

    private static final String SOURCE = 'AccountChangeEventHandler';

    /** Field whose change is the only reason this subscriber exists. */
    private static final String WATCHED_FIELD = 'BillingCountry';

    public static void handle(List<AccountChangeEvent> events) {
        // ---- Pass 1: decode headers. No SOQL, no DML. -----------------------------------------
        Map<String, Unit> unitsByKey = new Map<String, Unit>();

        for (AccountChangeEvent evt : events) {
            EventBus.ChangeEventHeader header = evt.ChangeEventHeader;

            // transactionKey groups a transaction; sequenceNumber orders the changes inside it.
            String dedupeKey = header.transactionKey + ':' + String.valueOf(header.sequenceNumber);
            Unit unit = unitsByKey.get(dedupeKey);
            if (unit == null) {
                unit = new Unit(dedupeKey, header);
                unitsByKey.put(dedupeKey, unit);
            }

            String changeType = header.changeType;

            if (changeType != null && changeType.startsWith('GAP_')) {
                // Covers GAP_CREATE, GAP_UPDATE, GAP_DELETE, GAP_UNDELETE and GAP_OVERFLOW
                // (apexrefguide L157298-157304). No field values to read — flag a resync.
                unit.needsResync = true;
                addIds(unit.resyncIds, unit.wildcards, header.recordIds);

            } else if (changeType == 'CREATE' || changeType == 'UNDELETE') {
                addIds(unit.hydrateIds, unit.wildcards, header.recordIds);

            } else if (changeType == 'UPDATE') {
                // changedFields is a decoded List<String> in Apex (apexrefguide L157340-157345)
                // and ALWAYS contains LastModifiedDate on an update (apexrefguide L157231-157232),
                // so "is it non-empty" is never a useful test. Ask for the field by name.
                List<String> changed = header.changedFields == null
                    ? new List<String>()
                    : header.changedFields;
                List<String> nulled = header.nulledFields == null
                    ? new List<String>()
                    : header.nulledFields;

                if (changed.contains(WATCHED_FIELD) || nulled.contains(WATCHED_FIELD)) {
                    addIds(unit.hydrateIds, unit.wildcards, header.recordIds);
                }

            } else if (changeType == 'DELETE') {
                // Do not query a deleted record. The ids are the whole payload.
                addIds(unit.deletedIds, unit.wildcards, header.recordIds);

            } else {
                // SNAPSHOT is reserved for future use (apexrefguide L157297); anything else is
                // a value this code was not written against. Never fall through silently.
                ApplicationLogger.warn(SOURCE, 'Unhandled changeType ' + changeType
                    + ' for ' + header.entityName + ' txn ' + header.transactionKey);
                unit.needsResync = true;
                addIds(unit.resyncIds, unit.wildcards, header.recordIds);
            }

            if (!unit.wildcards.isEmpty()) {
                // A wildcard means "every record of this object prefix changed" — a schema-level
                // conversion, not a row-level edit. Casting it to Id throws; treat it as a resync.
                unit.needsResync = true;
            }
        }

        if (unitsByKey.isEmpty()) {
            return;
        }

        // ---- Pass 2: drop units this subscriber already processed. One SOQL. -------------------
        Set<String> alreadySeen = new Set<String>();
        for (Change_Event_Receipt__c seen : [
            SELECT Dedupe_Key__c
            FROM Change_Event_Receipt__c
            WHERE Dedupe_Key__c IN :unitsByKey.keySet()
        ]) {
            alreadySeen.add(seen.Dedupe_Key__c);
        }

        Set<Id> hydrate = new Set<Id>();
        Set<Id> deleted = new Set<Id>();
        Set<Id> resync  = new Set<Id>();
        List<Change_Event_Receipt__c> receipts = new List<Change_Event_Receipt__c>();

        for (Unit unit : unitsByKey.values()) {
            if (alreadySeen.contains(unit.dedupeKey)) {
                continue;
            }
            hydrate.addAll(unit.hydrateIds);
            deleted.addAll(unit.deletedIds);
            resync.addAll(unit.resyncIds);
            receipts.add(unit.toReceipt());
        }

        if (receipts.isEmpty()) {
            return;
        }

        // ---- Pass 3: one query for current state, then hand off. -------------------------------
        if (!hydrate.isEmpty()) {
            // The event body is NOT a snapshot: unchanged fields arrive null, which is why
            // nulledFields exists at all (apexrefguide L157381-157385). Read the record.
            List<Account> current = [
                SELECT Id, Name, BillingCountry, AccountNumber, OwnerId
                FROM Account
                WHERE Id IN :hydrate
            ];
            AccountSyncQueueable.enqueueUpsert(current);
        }

        if (!deleted.isEmpty()) {
            AccountSyncQueueable.enqueueDelete(deleted);
        }

        if (!resync.isEmpty()) {
            ApplicationLogger.warn(SOURCE, 'Resync flagged for ' + resync.size()
                + ' Account id(s) after a gap or unknown change type');
        }

        // ---- Pass 4: record what was processed. One DML. ----------------------------------------
        // allOrNone = false: a duplicate Dedupe_Key__c means a concurrent invocation won the race
        // and already processed that unit. That is the expected outcome, not an error.
        Database.insert(receipts, false);

        ApplicationLogger.flush();
    }

    /**
     * Splits header.recordIds into real ids and wildcards. A wildcard is the object key prefix
     * followed by '*' (for accounts, '001*') and is emitted when a custom field type conversion
     * loses data (apexrefguide L157413-157417). Casting one to Id throws a System.StringException.
     */
    private static void addIds(Set<Id> target, Set<String> wildcards, List<String> recordIds) {
        if (recordIds == null) {
            return;
        }
        for (String raw : recordIds) {
            if (String.isBlank(raw)) {
                continue;
            }
            if (raw.endsWith('*')) {
                wildcards.add(raw);
                continue;
            }
            target.add((Id) raw);
        }
    }

    /** One transactionKey + sequenceNumber worth of work. */
    private class Unit {
        String dedupeKey;
        String entityName;
        String changeType;
        Long commitTimestamp;
        Set<Id> hydrateIds = new Set<Id>();
        Set<Id> deletedIds = new Set<Id>();
        Set<Id> resyncIds  = new Set<Id>();
        Set<String> wildcards = new Set<String>();
        Boolean needsResync = false;

        Unit(String dedupeKey, EventBus.ChangeEventHeader header) {
            this.dedupeKey = dedupeKey;
            this.entityName = header.entityName;
            this.changeType = header.changeType;
            this.commitTimestamp = header.commitTimestamp;
        }

        Change_Event_Receipt__c toReceipt() {
            return new Change_Event_Receipt__c(
                Dedupe_Key__c   = this.dedupeKey,
                Entity_Name__c  = this.entityName,
                Change_Type__c  = this.changeType,
                Needs_Resync__c = this.needsResync,
                // commitTimestamp is epoch milliseconds as a Long, not a Datetime
                // (apexrefguide L157321-157330).
                Commit_Time__c  = this.commitTimestamp == null
                    ? null
                    : Datetime.newInstance(this.commitTimestamp),
                Record_Ids__c   = String.join(new List<Id>(this.hydrateIds), ',')
            );
        }
    }
}
```

File: `AccountChangeEventHandler.cls-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<ApexClass xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>66.0</apiVersion>
    <status>Active</status>
</ApexClass>
```

**How to read it:**

- The dedupe key is `transactionKey + ':' + sequenceNumber`. `transactionKey` "uniquely identifies each Salesforce transaction" (`apexrefguide` L157438–157441) and `sequenceNumber` "is the sequence of the change within a transaction… starts from 1" (`apexrefguide` L157420–157426). A lead conversion emits four events under one `transactionKey` (`apexrefguide` L157429–157436), so keying on `transactionKey` alone would discard three of them.
- `commitNumber` looks like a better key and is not one: it "is not guaranteed to be unique in Salesforce — it is unique only in a single database instance" and may stop being sequential after an instance migration (`apexrefguide` L157306–157310). It is documented "for diagnostic purposes".
- The `else` branch is not defensive padding. `SNAPSHOT` is already listed as a reserved `changeType` (`apexrefguide` L157297), so an unrecognised value is a forward-compatibility event, not an impossible one.
- `ApplicationLogger.flush()` is called once, after the last DML — see `templates/apex/ApplicationLogger.cls`.
- `AccountSyncQueueable` is the callout hop. Callouts "must be made asynchronously from a trigger so that the trigger process isn't blocked" (`apexdev` L14900). Watch the enqueue budget: `System.enqueueJob` allows 50 calls in a synchronous context but **1** in an asynchronous one (`apexdev` L19571) — enqueue once per invocation, never once per event.

## Artifact 5 — the dedupe store (`Change_Event_Receipt__c`)

File: `force-app/main/default/objects/Change_Event_Receipt__c/Change_Event_Receipt__c.object-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CustomObject xmlns="http://soap.sforce.com/2006/04/metadata">
    <deploymentStatus>Deployed</deploymentStatus>
    <description>Idempotency receipt for processed change events, keyed on transactionKey + sequenceNumber.</description>
    <label>Change Event Receipt</label>
    <pluralLabel>Change Event Receipts</pluralLabel>
    <nameField>
        <displayFormat>CER-{0000000000}</displayFormat>
        <label>Receipt Number</label>
        <type>AutoNumber</type>
    </nameField>
    <sharingModel>Private</sharingModel>
</CustomObject>
```

File: `.../Change_Event_Receipt__c/fields/Dedupe_Key__c.field-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CustomField xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>Dedupe_Key__c</fullName>
    <caseSensitive>true</caseSensitive>
    <externalId>true</externalId>
    <label>Dedupe Key</label>
    <length>255</length>
    <required>true</required>
    <type>Text</type>
    <unique>true</unique>
</CustomField>
```

The remaining fields follow the same shape: `Entity_Name__c` Text(80), `Change_Type__c` Text(40),
`Record_Ids__c` LongTextArea(32768), `Needs_Resync__c` Checkbox, `Commit_Time__c` DateTime.

**How to read it:**

- `unique` plus `externalId` is what makes the pattern safe under concurrency. Two invocations that
  race on the same unit both try to insert; the database rejects the loser. `Database.insert(receipts, false)`
  turns that rejection into a row-level result instead of an exception that rolls back the batch.
- This is a "claim receipt", not an audit log. Give it a retention job — a subscriber that never
  deletes receipts turns its own dedupe query into the slowest thing in the trigger.
- UNVERIFIED (2026-09-05): the Apex Reference Guide does not state a maximum length for
  `transactionKey`. 255 is chosen because it is the Text field limit that still supports a unique
  index, not because the guide bounds the value. Confirm real key lengths in a sandbox before
  relying on the unique constraint.

## Artifact 6 — subscriber configuration (`AccountChangeEventTriggerConfig`)

File: `force-app/main/default/PlatformEventSubscriberConfigs/AccountChangeEventTriggerConfig.platformEventSubscriberConfig-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<PlatformEventSubscriberConfig xmlns="http://soap.sforce.com/2006/04/metadata">
    <platformEventConsumer>AccountChangeEventTrigger</platformEventConsumer>
    <batchSize>500</batchSize>
    <masterLabel>AccountChangeEventTriggerConfig</masterLabel>
    <user>integration.subscriber@example.com</user>
    <isProtected>false</isProtected>
</PlatformEventSubscriberConfig>
```

**How to read it:**

- `batchSize` is 1 through 2,000 and the default is 2,000; "We don't recommend setting the batch size to 1… Small batch sizes can slow down the processing of event messages" (`api_meta` L96416–96424). Lower it because a full batch will not fit in 6 MB of heap (`apexdev` L19577), not as a general precaution.
- Setting `user` moves the trigger off the Automated Process entity. The guide names four consequences: records are created as that user, `OwnerId` populates to that user, debug logs are created by that user, and **email can be sent, which is not supported from the default Automated Process user** (`api_meta` L96453–96465).
- `numPartitions` (1–10) and `partitionKey` exist in API 62.0 and later (`api_meta` L96434–96452), but `partitionKey` is documented as the standard `EventUuid` field or a required custom field of the **custom platform event** the trigger subscribes to. A change event is not a custom platform event and has no `EventUuid`.
  - UNVERIFIED (2026-09-05): `api_meta` L96385–96386 scopes this whole type to "a platform event Apex trigger". That change event triggers are also configurable this way is stated only in the Change Data Capture Developer Guide, which is not in the grounding corpus. If the deploy is rejected, that is the answer.

## Artifact 7 — the test class (`AccountChangeEventHandlerTest.cls`)

```apex
@IsTest
private class AccountChangeEventHandlerTest {

    /**
     * Test.enableChangeDataCapture() "ensures that Apex tests can fire change event triggers
     * regardless of the entities selected in Setup in the Change Data Capture page" and must be
     * called "at the beginning of your test before performing DML operations and calling
     * Test.getEventBus().deliver()" (apexrefguide L240419-240435). It does not change the Setup
     * selection, so a green test proves nothing about whether the entity is enabled in the org.
     */

    @IsTest
    static void createEventProducesOneReceipt() {
        Test.enableChangeDataCapture();

        Test.startTest();
        Account a = new Account(Name = 'CDC Create', BillingCountry = 'US');
        insert a;
        Test.getEventBus().deliver();
        Test.stopTest();

        List<Change_Event_Receipt__c> receipts = [
            SELECT Dedupe_Key__c, Change_Type__c, Entity_Name__c, Needs_Resync__c, Record_Ids__c
            FROM Change_Event_Receipt__c
        ];
        Assert.areEqual(1, receipts.size(), 'One CREATE event should leave exactly one receipt');
        Assert.areEqual('CREATE', receipts[0].Change_Type__c, 'changeType should be CREATE');
        Assert.areEqual('Account', receipts[0].Entity_Name__c, 'entityName should be Account');
        Assert.isFalse(receipts[0].Needs_Resync__c, 'A CREATE is not a gap');
        Assert.isTrue(receipts[0].Record_Ids__c.contains(a.Id), 'The new id should be recorded');
        // transactionKey ':' sequenceNumber — sequenceNumber starts at 1 (apexrefguide L157421).
        Assert.isTrue(receipts[0].Dedupe_Key__c.endsWith(':1'), 'First change in the txn is sequence 1');
    }

    @IsTest
    static void updateOfWatchedFieldHydratesAndDedupes() {
        Test.enableChangeDataCapture();

        Account a = new Account(Name = 'CDC Update', BillingCountry = 'US');
        insert a;
        Test.getEventBus().deliver();          // drain the CREATE event first
        delete [SELECT Id FROM Change_Event_Receipt__c];

        Test.startTest();
        a.BillingCountry = 'CA';
        update a;
        Test.getEventBus().deliver();
        Test.stopTest();

        List<Change_Event_Receipt__c> receipts = [
            SELECT Dedupe_Key__c, Change_Type__c, Record_Ids__c
            FROM Change_Event_Receipt__c
        ];
        Assert.areEqual(1, receipts.size(), 'One UPDATE event should leave exactly one receipt');
        Assert.areEqual('UPDATE', receipts[0].Change_Type__c, 'changeType should be UPDATE');
        Assert.isTrue(
            receipts[0].Record_Ids__c.contains(a.Id),
            'BillingCountry is the watched field, so the record should have been hydrated'
        );

        // Idempotency: replaying the same unit must not produce a second receipt.
        String key = receipts[0].Dedupe_Key__c;
        Test.startTest();
        Database.SaveResult sr = Database.insert(
            new Change_Event_Receipt__c(Dedupe_Key__c = key, Entity_Name__c = 'Account'),
            false
        );
        Test.stopTest();
        Assert.isFalse(sr.isSuccess(), 'The unique Dedupe_Key__c index must reject the replay');
    }

    @IsTest
    static void unrelatedFieldChangeIsIgnored() {
        Test.enableChangeDataCapture();

        Account a = new Account(Name = 'CDC Noise', BillingCountry = 'US');
        insert a;
        Test.getEventBus().deliver();
        delete [SELECT Id FROM Change_Event_Receipt__c];

        Test.startTest();
        a.Description = 'edited something the subscriber does not watch';
        update a;
        Test.getEventBus().deliver();
        Test.stopTest();

        List<Change_Event_Receipt__c> receipts = [
            SELECT Record_Ids__c FROM Change_Event_Receipt__c
        ];
        Assert.areEqual(1, receipts.size(), 'The event is still received and still receipted');
        Assert.isTrue(
            String.isBlank(receipts[0].Record_Ids__c),
            'changedFields did not contain BillingCountry, so nothing should have been hydrated'
        );
    }
}
```

File: `AccountChangeEventHandlerTest.cls-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<ApexClass xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>66.0</apiVersion>
    <status>Active</status>
</ApexClass>
```

**How to read it:**

- Delivery is explicit. `Test.stopTest()` does not flush the event bus for you — the guide pairs
  `enableChangeDataCapture()` with an explicit `Test.getEventBus().deliver()` call (`apexrefguide` L240421–240423),
  and adds that each downstream process that publishes again needs its own `deliver()` (`apexdev` L17936–17939).
- Two `deliver()` calls in the UPDATE test are deliberate: the insert produces a CREATE event that
  would otherwise arrive in the same drain and make the assertion ambiguous.
- **GAP and OVERFLOW are not covered here, and cannot honestly be.** UNVERIFIED (2026-09-05): the only
  in-corpus example that constructs a change event in Apex and publishes it (`new Products__ChangeEvent()`,
  `EventBus.publish(event)`, `apexdev` L29657–29680) is from **External** Change Data Capture over an
  OData 4.0 connection, not platform CDC on a Salesforce object. Whether `new AccountChangeEvent()` can
  be instantiated and published in a test is not stated in the Apex Developer Guide or the Apex Reference
  Guide. Do not write a GAP test that silently passes because the event never arrived — assert on the
  handler's effect, or extract the GAP branch into a `@TestVisible` method and call it directly.
- Use `templates/apex/tests/TestDataFactory.cls` for the `Account` fixtures once this test class grows
  past the three cases above.

## Artifact 8 — `package.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>Change_Event_Receipt__c</members>
        <members>Application_Log__c</members>
        <name>CustomObject</name>
    </types>
    <types>
        <members>Change_Event_Receipt__c.Dedupe_Key__c</members>
        <members>Change_Event_Receipt__c.Entity_Name__c</members>
        <members>Change_Event_Receipt__c.Change_Type__c</members>
        <members>Change_Event_Receipt__c.Record_Ids__c</members>
        <members>Change_Event_Receipt__c.Needs_Resync__c</members>
        <members>Change_Event_Receipt__c.Commit_Time__c</members>
        <name>CustomField</name>
    </types>
    <types>
        <members>ChangeEvents_AccountChangeEvent</members>
        <name>PlatformEventChannelMember</name>
    </types>
    <types>
        <members>AccountChangeEventHandler</members>
        <members>AccountChangeEventHandlerTest</members>
        <members>AccountSyncQueueable</members>
        <members>ApplicationLogger</members>
        <name>ApexClass</name>
    </types>
    <types>
        <members>AccountChangeEventTrigger</members>
        <name>ApexTrigger</name>
    </types>
    <types>
        <members>AccountChangeEventTriggerConfig</members>
        <name>PlatformEventSubscriberConfig</name>
    </types>
    <version>66.0</version>
</Package>
```

The `<members>` value for a channel member is the component full name in `ChannelName_EventName`
format (`api_meta` L96161–96170).

## Deploy order

`PlatformEventSubscriberConfig` "references an Apex trigger, which depends on a platform event. If the
referenced items exist in the Salesforce org, you can deploy the… component" — otherwise the deployment
fails (`api_meta` L96482–96486). The same dependency chain applies here, so order matters:

1. `CustomObject` + `CustomField` — `Change_Event_Receipt__c` and `Application_Log__c`. Nothing compiles without them.
2. `PlatformEventChannelMember` — enables `AccountChangeEvent`. The trigger will compile without it but will never fire.
3. `ApexClass` — `ApplicationLogger`, `AccountSyncQueueable`, `AccountChangeEventHandler`.
4. `ApexTrigger` — `AccountChangeEventTrigger`.
5. `PlatformEventSubscriberConfig` — last, because it names the trigger by full name.
6. Grant the running user (Automated Process, or the `user` from Artifact 6) read on `Account` and
   create on `Change_Event_Receipt__c` and `Application_Log__c`.

```bash
# validate the whole slice with tests, deploy nothing
sf project deploy validate \
  --manifest manifest/package.xml \
  --test-level RunSpecifiedTests \
  --tests AccountChangeEventHandlerTest

# deploy
sf project deploy start --manifest manifest/package.xml

# pull the channel selection back after someone changes it on the Setup page
sf project retrieve start \
  --metadata PlatformEventChannelMember:ChangeEvents_AccountChangeEvent
```

## Verification

Run the checker and the tests, then prove the subscription is live — the tests cannot do that, because
`Test.enableChangeDataCapture()` fires triggers "regardless of the entities selected in Setup"
(`apexrefguide` L240433–240435).

```bash
python3 skills/apex/change-data-capture-apex/scripts/check_change_data_capture_apex.py \
  --manifest-dir force-app/main/default

sf apex run test --tests AccountChangeEventHandlerTest --result-format human --wait 10
```

1. **Is the entity actually selected?** Retrieve `PlatformEventChannelMember:ChangeEvents_AccountChangeEvent`.
   A retrieve that comes back empty means the trigger is deployed and dead.

2. **Did a real change produce a receipt?** Update one Account in the org, wait, then:

   ```sql
   SELECT Dedupe_Key__c, Entity_Name__c, Change_Type__c, Needs_Resync__c, Commit_Time__c
   FROM Change_Event_Receipt__c
   ORDER BY CreatedDate DESC
   LIMIT 20
   ```

3. **Are gaps happening?** `SELECT COUNT(Id) FROM Change_Event_Receipt__c WHERE Needs_Resync__c = true`
   over a rolling window. A non-zero count that nobody looks at is exactly the silent drift this
   subscriber exists to prevent.

4. **Where are the logs?** Not in the Developer Console. Set a trace flag on the Automated Process
   entity, or set `user` in Artifact 6 so "debug logs for the trigger execution are created by this
   user" (`api_meta` L96464).
