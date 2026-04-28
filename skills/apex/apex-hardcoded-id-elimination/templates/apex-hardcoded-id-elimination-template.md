# Template — ID Lookup Helper Class

A canonical Apex helper class that demonstrates all four lookup mechanisms with proper caching. Copy, rename, and adapt to your project. Do not edit this template in-place.

---

## `IdLookup.cls`

```apex
/**
 * Centralized, cached lookup for Salesforce record IDs.
 * Eliminates hardcoded ID literals from Apex.
 *
 * Mechanisms covered:
 *   (1) RecordType  -- Schema describe (no SOQL cost)
 *   (2) Profile     -- SOQL by Name, cached per-transaction
 *   (3) Queue/Group -- SOQL by DeveloperName, cached per-transaction
 *   (4) Config IDs  -- Custom Metadata Type, no caching needed (built-in)
 */
public with sharing class IdLookup {

    // -- RecordType: describe-API based ----------------------------------

    private static final Map<String, Map<String, Id>> RT_CACHE = new Map<String, Map<String, Id>>();

    /**
     * Resolve a RecordType Id by SObject + DeveloperName.
     * Uses Schema describe -- no SOQL cost.
     * Throws IdLookupException if the DeveloperName is unknown.
     */
    public static Id recordTypeId(SObjectType sot, String developerName) {
        String key = String.valueOf(sot);
        if (!RT_CACHE.containsKey(key)) {
            Map<String, Id> byDevName = new Map<String, Id>();
            Map<String, Schema.RecordTypeInfo> infos =
                sot.getDescribe().getRecordTypeInfosByDeveloperName();
            for (String dn : infos.keySet()) {
                byDevName.put(dn, infos.get(dn).getRecordTypeId());
            }
            RT_CACHE.put(key, byDevName);
        }
        Id rtId = RT_CACHE.get(key).get(developerName);
        if (rtId == null) {
            throw new IdLookupException(
                'Unknown RecordType DeveloperName "' + developerName +
                '" on SObject ' + key);
        }
        return rtId;
    }

    // -- Profile: SOQL by Name, cached -----------------------------------

    private static Map<String, Id> profileIdByName;

    public static Id profileId(String name) {
        if (profileIdByName == null) {
            profileIdByName = new Map<String, Id>();
            for (Profile p : [SELECT Id, Name FROM Profile]) {
                profileIdByName.put(p.Name, p.Id);
            }
        }
        Id pid = profileIdByName.get(name);
        if (pid == null) {
            throw new IdLookupException('No Profile with Name "' + name + '" in this org');
        }
        return pid;
    }

    // -- Queue / Group: SOQL by DeveloperName, cached --------------------

    private static Map<String, Id> queueIdByDevName;

    public static Id queueId(String developerName) {
        if (queueIdByDevName == null) {
            queueIdByDevName = new Map<String, Id>();
            for (Group g : [SELECT Id, DeveloperName FROM Group WHERE Type = 'Queue']) {
                queueIdByDevName.put(g.DeveloperName, g.Id);
            }
        }
        Id qid = queueIdByDevName.get(developerName);
        if (qid == null) {
            throw new IdLookupException(
                'No Queue with DeveloperName "' + developerName + '" in this org');
        }
        return qid;
    }

    private static Map<String, Id> groupIdByDevName;

    public static Id publicGroupId(String developerName) {
        if (groupIdByDevName == null) {
            groupIdByDevName = new Map<String, Id>();
            for (Group g : [SELECT Id, DeveloperName FROM Group WHERE Type = 'Regular']) {
                groupIdByDevName.put(g.DeveloperName, g.Id);
            }
        }
        return groupIdByDevName.get(developerName);
    }

    // -- Custom Metadata: deferred to caller's getInstance() -------------

    /**
     * For configurable IDs (default Account, fallback User, routing Queue),
     * define a Custom Metadata Type and call:
     *
     *   RoutingConfig__mdt cfg = RoutingConfig__mdt.getInstance('CaseRouter');
     *   Id queueId = cfg.DefaultQueue__c;
     *
     * No helper needed -- getInstance is already cached at platform level.
     */

    public class IdLookupException extends Exception {}
}
```

---

## Usage

```apex
// RecordType
Id partnerRt = IdLookup.recordTypeId(Account.SObjectType, 'Partner');

// Profile
Id sysAdmin = IdLookup.profileId('System Administrator');

// Queue
Id tier2Queue = IdLookup.queueId('Tier2_Support');

// Custom Metadata
RoutingConfig__mdt cfg = RoutingConfig__mdt.getInstance('CaseRouter');
Id defaultQueue = cfg.DefaultQueue__c;
```

---

## Test class (`IdLookupTest.cls`)

```apex
@IsTest
private class IdLookupTest {

    @IsTest
    static void profileId_throws_for_unknown() {
        Boolean threw = false;
        try {
            IdLookup.profileId('No Such Profile Definitely Not Real');
        } catch (IdLookup.IdLookupException e) {
            threw = true;
        }
        System.assert(threw, 'Expected IdLookupException for unknown Profile name');
    }

    @IsTest
    static void queueId_resolves_after_insert() {
        Group q = new Group(Name = 'Test Q', DeveloperName = 'Test_Q', Type = 'Queue');
        insert q;
        // Cache is per-transaction; the first call to queueId() will populate
        // the cache including the new Queue inserted above.
        System.assertEquals(q.Id, IdLookup.queueId('Test_Q'));
    }

    @IsTest
    static void recordTypeId_throws_for_unknown_devname() {
        Boolean threw = false;
        try {
            IdLookup.recordTypeId(Account.SObjectType, 'No_Such_RT_DeveloperName');
        } catch (IdLookup.IdLookupException e) {
            threw = true;
        }
        System.assert(threw, 'Expected IdLookupException for unknown RecordType DeveloperName');
    }
}
```

---

## Verification

After deploying `IdLookup.cls`:

1. Run `python3 scripts/check_apex_hardcoded_id_elimination.py --src force-app/main/default/classes` and confirm zero P0/P1 findings on the helper itself.
2. Run all tests; the `IdLookupTest` class proves resolution and error paths work.
3. Grep the rest of the project for the Salesforce-ID regex; every hit should now route through `IdLookup` or a `__mdt.getInstance()` call.
4. Confirm no caller stores a returned ID in a `String` variable.
