# Examples: Apex Trigger Framework

---

## Example 1: Complete Single-Trigger Pattern with Activation Bypass

```apex
// AccountTrigger.trigger
trigger AccountTrigger on Account (
    before insert, before update, before delete,
    after insert, after update, after delete, after undelete
) {
    // Activation bypass — disable without deployment
    Trigger_Setting__mdt[] settings = [
        SELECT Is_Active__c FROM Trigger_Setting__mdt
        WHERE Object_API_Name__c = 'Account' LIMIT 1
    ];
    if (!settings.isEmpty() && !settings[0].Is_Active__c) return;

    AccountTriggerHandler handler = new AccountTriggerHandler();
    if (Trigger.isBefore) {
        if (Trigger.isInsert) handler.onBeforeInsert(Trigger.new);
        if (Trigger.isUpdate) handler.onBeforeUpdate(Trigger.new, Trigger.oldMap);
        if (Trigger.isDelete) handler.onBeforeDelete(Trigger.old);
    }
    if (Trigger.isAfter) {
        if (Trigger.isInsert)   handler.onAfterInsert(Trigger.new);
        if (Trigger.isUpdate)   handler.onAfterUpdate(Trigger.new, Trigger.oldMap);
        if (Trigger.isDelete)   handler.onAfterDelete(Trigger.oldMap);
        if (Trigger.isUndelete) handler.onAfterUndelete(Trigger.new);
    }
}
```

---

## Example 2: Handler with Recursion Guard and Delta Check

```apex
public with sharing class AccountTriggerHandler {

    // Set-based recursion guard — tracks processed record IDs
    // More precise than a boolean flag (which blocks all re-entry)
    private static Set<Id> processedIds = new Set<Id>();

    public void onBeforeUpdate(List<Account> newAccounts, Map<Id, Account> oldMap) {
        // Delta check — only process records where Status changed
        List<Account> statusChanged = new List<Account>();
        for (Account acc : newAccounts) {
            if (acc.Status__c != oldMap.get(acc.Id).Status__c) {
                statusChanged.add(acc);
            }
        }
        if (statusChanged.isEmpty()) return; // Nothing to do

        AccountService.handleStatusChange(statusChanged, oldMap);
    }

    public void onAfterInsert(List<Account> newAccounts) {
        // Recursion guard — filter out records already processed this transaction
        List<Account> toProcess = new List<Account>();
        for (Account acc : newAccounts) {
            if (!processedIds.contains(acc.Id)) {
                processedIds.add(acc.Id);
                toProcess.add(acc);
            }
        }
        if (toProcess.isEmpty()) return;

        // Safe to do DML on related objects in after insert
        AccountService.createDefaultContacts(toProcess);
    }

    // Explicitly declare unused contexts as no-ops
    public void onBeforeInsert(List<Account> newAccounts) {}
    public void onBeforeDelete(List<Account> oldAccounts) {}
    public void onAfterUpdate(List<Account> newAccounts, Map<Id, Account> oldMap) {}
    public void onAfterDelete(Map<Id, Account> oldMap) {}
    public void onAfterUndelete(List<Account> newAccounts) {}
}
```

**Why set-based over boolean**: A boolean flag (`static Boolean hasRun = false`) blocks ALL re-entry, even legitimate re-entry of different records. A Set<Id> only blocks the exact records already processed — new records added in the same transaction are still handled.

---

## Example 3: Test Class — Bulk, Sharing, and Negative Tests

```apex
@isTest
private class AccountTriggerHandlerTest {

    @TestSetup
    static void setupTestData() {
        // Reset static recursion guard between tests
        // (call a test utility that resets the static set if your handler exposes a reset method)

        // Create test users for sharing tests
        Profile p = [SELECT Id FROM Profile WHERE Name = 'Standard User' LIMIT 1];
        User restrictedUser = new User(
            FirstName = 'Test', LastName = 'User',
            Email = 'testuser@example.com.test',
            Username = 'testuser@example.com.test',
            Alias = 'tuser',
            ProfileId = p.Id,
            TimeZoneSidKey = 'America/New_York',
            LocaleSidKey = 'en_US',
            EmailEncodingKey = 'UTF-8',
            LanguageLocaleKey = 'en_US'
        );
        insert restrictedUser;
    }

    // ✅ Positive test — single record
    @isTest
    static void testStatusChange_singleRecord_createsRelatedRecord() {
        Account acc = TestDataFactory.createAccount('Test Corp', 'Prospect');
        insert acc;

        Test.startTest();
        acc.Status__c = 'Active';
        update acc;
        Test.stopTest();

        List<Contact> contacts = [SELECT Id FROM Contact WHERE AccountId = :acc.Id];
        System.assertEquals(1, contacts.size(), 'Expected 1 default Contact created on status change');
    }

    // ✅ Bulk test — 200 records (required)
    @isTest
    static void testStatusChange_bulkRecords_noGovernorLimitErrors() {
        List<Account> accounts = TestDataFactory.createAccounts(200, 'Prospect');
        insert accounts;

        Test.startTest();
        for (Account acc : accounts) {
            acc.Status__c = 'Active';
        }
        update accounts;
        Test.stopTest();

        List<Contact> contacts = [SELECT Id FROM Contact WHERE AccountId IN :accounts];
        System.assertEquals(200, contacts.size(), 'Expected 200 Contacts for 200 Accounts');
    }

    // ✅ Negative test — no status change should not create contacts
    @isTest
    static void testNoStatusChange_doesNotCreateContacts() {
        Account acc = TestDataFactory.createAccount('Test Corp', 'Active');
        insert acc;

        Test.startTest();
        acc.Name = 'Updated Name'; // Change something other than Status
        update acc;
        Test.stopTest();

        List<Contact> contacts = [SELECT Id FROM Contact WHERE AccountId = :acc.Id];
        System.assertEquals(0, contacts.size(), 'No Contacts should be created when Status does not change');
    }

    // ✅ Sharing test — must use System.runAs()
    @isTest
    static void testStatusChange_restrictedUser_respectsSharing() {
        User restrictedUser = [SELECT Id FROM User WHERE Username = 'testuser@example.com.test' LIMIT 1];

        Account acc;
        System.runAs(new User(Id = UserInfo.getUserId())) {
            acc = TestDataFactory.createAccount('Test Corp', 'Prospect');
            insert acc;
            // Note: don't share the Account with restrictedUser — test sharing enforcement
        }

        System.runAs(restrictedUser) {
            Test.startTest();
            try {
                acc.Status__c = 'Active';
                update acc; // Should fail — restrictedUser doesn't own this record
                System.assert(false, 'Expected exception was not thrown');
            } catch (DmlException e) {
                System.assert(e.getMessage().contains('INSUFFICIENT_ACCESS'),
                    'Expected sharing violation, got: ' + e.getMessage());
            }
            Test.stopTest();
        }
    }
}
```

---

## Example 4: Bulk-Safe Related-Record Lookup (Set → SOQL IN → Map → Correlate)

The examples above only compare each record against its own prior state via `oldMap`.
The other half of bulk safety is querying *related* records without a SOQL statement
per row. The canonical idiom in the Apex Developer Guide is: collect the distinct
foreign-key IDs from `Trigger.new` into a `Set`, run **one** SOQL query with an `IN`
clause, index the results in a `Map` keyed by `Id`, then loop a second time to correlate.

```apex
public with sharing class OpportunityLineItemTriggerHandler {

    // Before insert: stamp each line item with data from its PricebookEntry.
    // One query serves the whole batch — never query inside the loop.
    public void onBeforeInsert(List<OpportunityLineItem> newLines) {

        // 1. Collect distinct related IDs into a Set (dedupes automatically).
        Set<Id> pricebookEntryIds = new Set<Id>();
        for (OpportunityLineItem oli : newLines) {
            if (oli.PricebookEntryId != null) {
                pricebookEntryIds.add(oli.PricebookEntryId);
            }
        }
        if (pricebookEntryIds.isEmpty()) return;

        // 2. One SOQL query with an IN clause against the Set,
        //    indexed by Id in a Map (a SOQL-into-Map does this in one step).
        Map<Id, PricebookEntry> entriesById = new Map<Id, PricebookEntry>([
            SELECT Id, UnitPrice, Product2Id
            FROM PricebookEntry
            WHERE Id IN :pricebookEntryIds
        ]);

        // 3. Second loop — correlate each record with its queried data by Id.
        for (OpportunityLineItem oli : newLines) {
            PricebookEntry entry = entriesById.get(oli.PricebookEntryId);
            if (entry != null) {
                oli.List_Price_Snapshot__c = entry.UnitPrice;
            }
        }
    }
}
```

**Correlating with `Trigger.newMap` / `Trigger.oldMap`**: when the related query
returns child records that point *back* at the triggering records, use
`Trigger.newMap` (insert/update) or `Trigger.oldMap` (update/delete) — both are
`Id`-to-sObject maps — to link the query results to the originating record without a
nested loop. For example, `Trigger.oldMap.keySet()` yields the exact set of IDs to
feed into a child query's `IN` clause, and each child's parent lookup then indexes
straight back into the map. `keySet()` is also the cleanest way to build the `Set<Id>`
in step 1 when the foreign key is the triggering record's own Id.

**Why this matters**: querying inside the loop (`SELECT ... WHERE Id = :oli.PricebookEntryId`
per row) burns one of the 100 SOQL statements per record and fails the moment Data
Loader, the Bulk API, or an integration sends a batch. The Set → IN → Map idiom is
constant in SOQL cost regardless of batch size.
