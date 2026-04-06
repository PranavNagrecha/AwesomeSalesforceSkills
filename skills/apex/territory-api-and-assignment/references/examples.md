# Examples — Territory API and Assignment

## Example 1: Onboarding a New Sales Rep — Assign User to Multiple Territories

**Context:** A new Account Executive joins and must be immediately added to three territories (Pacific Northwest, Mountain West, and National Accounts) as part of an automated onboarding flow triggered by an HR system integration.

**Problem:** Without this skill's guidance, a practitioner might use a raw `insert` statement. When one of the three territories already has the user (e.g., they were manually added in Setup before the automation ran), the entire transaction rolls back with `DUPLICATE_VALUE` and none of the assignments succeed.

**Solution:**

```apex
public class TerritoryOnboardingService {

    public static void assignRepToTerritories(Id userId, List<Id> territory2Ids) {
        // Step 1: find which assignments already exist
        Set<Id> existingTerritoryIds = new Set<Id>();
        for (UserTerritory2Association existing :
                [SELECT Territory2Id FROM UserTerritory2Association
                 WHERE UserId = :userId AND Territory2Id IN :territory2Ids]) {
            existingTerritoryIds.add(existing.Territory2Id);
        }

        // Step 2: build net-new list
        List<UserTerritory2Association> toInsert = new List<UserTerritory2Association>();
        for (Id tId : territory2Ids) {
            if (!existingTerritoryIds.contains(tId)) {
                toInsert.add(new UserTerritory2Association(
                    UserId           = userId,
                    Territory2Id     = tId,
                    RoleInTerritory2 = 'Account Executive'
                ));
            }
        }

        // Step 3: partial-success insert — handle any remaining duplicates gracefully
        if (!toInsert.isEmpty()) {
            List<Database.SaveResult> results = Database.insert(toInsert, false);
            List<String> failures = new List<String>();
            for (Database.SaveResult sr : results) {
                if (!sr.isSuccess()) {
                    for (Database.Error err : sr.getErrors()) {
                        if (err.getStatusCode() != StatusCode.DUPLICATE_VALUE) {
                            failures.add(err.getMessage());
                        }
                    }
                }
            }
            if (!failures.isEmpty()) {
                throw new TerritoryAssignmentException(
                    'Territory assignment failed: ' + String.join(failures, '; ')
                );
            }
        }
    }

    public class TerritoryAssignmentException extends Exception {}
}
```

**Why it works:** Pre-querying existing associations eliminates the majority of `DUPLICATE_VALUE` conditions before they reach the DML layer. The `Database.insert(list, false)` pattern provides a last-resort safety net for race conditions (e.g., a concurrent Setup UI assignment) and lets remaining rows succeed even if one record is a duplicate.

---

## Example 2: Bulk Account-Territory Pin After a Territory Realignment Migration

**Context:** After an ETM model restructure, 5,000 key accounts must be pinned to their new territories via a data migration. The accounts are loaded from a CSV that maps `Account_External_ID__c` to `Territory_Name__c`. The migration runs in Batch Apex because it exceeds synchronous governor limits.

**Problem:** A practitioner might try to trigger assignment rule evaluation from inside the Batch Apex `execute` method by calling `UserInfo.getSessionId()` to build a SOAP callout. The session ID returns `null` in async context, causing the callout to fail silently or throw a `CalloutException`.

**Solution:**

```apex
// Batch class handles the DML-only step (async-safe)
// Rule evaluation is deferred to a synchronous Platform Event subscriber
global class TerritoryPinBatch implements Database.Batchable<SObject> {

    global Database.QueryLocator start(Database.BatchableContext bc) {
        return Database.getQueryLocator(
            'SELECT Id, Territory2_External_Id__c FROM Account ' +
            'WHERE Needs_Territory_Pin__c = true'
        );
    }

    global void execute(Database.BatchableContext bc, List<Account> scope) {
        Set<String> extIds = new Set<String>();
        for (Account a : scope) {
            if (a.Territory2_External_Id__c != null) {
                extIds.add(a.Territory2_External_Id__c);
            }
        }

        Map<String, Id> extIdToTerritory2Id = new Map<String, Id>();
        for (Territory2 t :
                [SELECT Id, ExternalId__c FROM Territory2
                 WHERE ExternalId__c IN :extIds]) {
            extIdToTerritory2Id.put(t.ExternalId__c, t.Id);
        }

        // Remove stale manual associations for these accounts first
        List<ObjectTerritory2Association> stale =
            [SELECT Id FROM ObjectTerritory2Association
             WHERE ObjectId IN :scope AND AssociationCause = 'Territory'];
        if (!stale.isEmpty()) {
            delete stale;
        }

        // Build new associations
        List<ObjectTerritory2Association> toInsert = new List<ObjectTerritory2Association>();
        for (Account a : scope) {
            Id t2Id = extIdToTerritory2Id.get(a.Territory2_External_Id__c);
            if (t2Id != null) {
                toInsert.add(new ObjectTerritory2Association(
                    ObjectId         = a.Id,
                    Territory2Id     = t2Id,
                    AssociationCause = 'Territory'
                ));
            }
        }
        Database.insert(toInsert, false);

        // NOTE: Do NOT call SOAP rule evaluation here.
        // UserInfo.getSessionId() is null in async context.
    }

    global void finish(Database.BatchableContext bc) {
        // Publish Platform Event — synchronous subscriber performs the SOAP callout
        EventBus.publish(new Territory_Repin_Complete__e());
    }
}
```

**Why it works:** The batch class handles only the DML-safe portion: deleting stale manual associations and inserting fresh ones. Rule evaluation is deferred to a synchronous Platform Event subscriber where `UserInfo.getSessionId()` returns a valid token. This separates the async-safe DML path from the sync-only callout path.

---

## Anti-Pattern: Using a Trigger on ObjectTerritory2Association

**What practitioners do:** They write an Apex trigger on `ObjectTerritory2Association` with `after insert` logic to fire downstream processes (e.g., update a custom field on the Account, send a notification) whenever an account is added to a territory.

```apex
// THIS WILL NEVER FIRE — triggers do not execute on ObjectTerritory2Association
trigger TerritoryAssociationTrigger on ObjectTerritory2Association (after insert) {
    for (ObjectTerritory2Association ota : Trigger.new) {
        // This code will never run — not from Apex DML, not from Setup
        System.debug('Account ' + ota.ObjectId + ' assigned to ' + ota.Territory2Id);
    }
}
```

**What goes wrong:** The trigger deploys without error. No compile-time or deploy-time warning is produced. At runtime, the trigger body is simply never invoked. Practitioners spend significant time debugging why their trigger is not being called.

**Correct approach:** Dispatch a Platform Event from the Apex code that writes the `ObjectTerritory2Association` record, and subscribe to that event in a trigger or flow to perform downstream processing.

```apex
// In the service that creates associations
List<ObjectTerritory2Association> toInsert = buildAssociations(...);
Database.insert(toInsert, false);

// Publish a Platform Event to signal downstream logic
List<Territory_Account_Assigned__e> events = new List<Territory_Account_Assigned__e>();
for (ObjectTerritory2Association ota : toInsert) {
    events.add(new Territory_Account_Assigned__e(
        Account_Id__c   = ota.ObjectId,
        Territory_Id__c = ota.Territory2Id
    ));
}
EventBus.publish(events);
```
