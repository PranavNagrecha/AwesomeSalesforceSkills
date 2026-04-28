# Examples — Apex Hardcoded ID Elimination

Three end-to-end refactors showing how to eliminate hardcoded IDs.

---

## Example 1 — Profile-based logic

### Before (broken across orgs)

```apex
public class FeatureGate {
    // 15-char prod ID — different in every sandbox and scratch org
    private static final String SYSADMIN_PROFILE_ID = '00e1x000000ABcD';

    public static Boolean isAdmin(Id userId) {
        User u = [SELECT ProfileId FROM User WHERE Id = :userId LIMIT 1];
        return u.ProfileId == SYSADMIN_PROFILE_ID;  // also fails 15/18 comparison
    }
}
```

Two bugs: hardcoded ID and `String == Id` comparison.

### After (cached, name-based, typed)

```apex
public class FeatureGate {
    private static Map<String, Id> profileIdByName;

    private static Id profileId(String name) {
        if (profileIdByName == null) {
            profileIdByName = new Map<String, Id>();
            for (Profile p : [SELECT Id, Name FROM Profile]) {
                profileIdByName.put(p.Name, p.Id);
            }
        }
        return profileIdByName.get(name);
    }

    public static Boolean isAdmin(Id userId) {
        User u = [SELECT ProfileId FROM User WHERE Id = :userId LIMIT 1];
        return u.ProfileId == profileId('System Administrator');
    }
}
```

For subscriber-org safety, prefer driving the profile name from a Custom Metadata Type entry (`AdminProfile__mdt.Name__c`) so admin teams can override per-org.

---

## Example 2 — RecordType assignment in a trigger handler

### Before

```apex
public class AccountTriggerHandler {
    private static final Id PARTNER_RT_ID = '012xx0000004C9I';   // sandbox-specific

    public void beforeInsert(List<Account> accounts) {
        for (Account a : accounts) {
            if (a.Type == 'Partner') {
                a.RecordTypeId = PARTNER_RT_ID;
            }
        }
    }
}
```

### After (describe-driven)

```apex
public class AccountTriggerHandler {
    private static final Id PARTNER_RT_ID = Schema.SObjectType.Account
        .getRecordTypeInfosByDeveloperName()
        .get('Partner')
        .getRecordTypeId();

    public void beforeInsert(List<Account> accounts) {
        for (Account a : accounts) {
            if (a.Type == 'Partner') {
                a.RecordTypeId = PARTNER_RT_ID;
            }
        }
    }
}
```

Describe is metadata-driven; the same code resolves the correct RecordType in every org. No SOQL cost.

---

## Example 3 — Group/Queue assignment for Case routing

### Before

```apex
public class CaseRouter {
    private static final Id TIER1_QUEUE_ID = '00G3x000003abcD';
    private static final Id TIER2_QUEUE_ID = '00G3x000003efgH';

    public static void route(List<Case> cases) {
        for (Case c : cases) {
            c.OwnerId = (c.Priority == 'High') ? TIER2_QUEUE_ID : TIER1_QUEUE_ID;
        }
    }
}
```

Three problems: hardcoded IDs, no env portability, no admin override.

### After (DeveloperName-cached, CMDT-driven priority mapping)

```apex
public class CaseRouter {
    private static Map<String, Id> queueIdByDevName;

    private static Id queueId(String devName) {
        if (queueIdByDevName == null) {
            queueIdByDevName = new Map<String, Id>();
            for (Group g : [SELECT Id, DeveloperName FROM Group WHERE Type = 'Queue']) {
                queueIdByDevName.put(g.DeveloperName, g.Id);
            }
        }
        return queueIdByDevName.get(devName);
    }

    public static void route(List<Case> cases) {
        for (Case c : cases) {
            CaseRouting__mdt cfg = CaseRouting__mdt.getInstance(c.Priority);
            c.OwnerId = queueId(cfg.QueueDeveloperName__c);
        }
    }
}
```

Now: zero ID literals, single SOQL per transaction, admins re-target queues by editing CMDT.

---

## Example 4 — Test class with no hardcoded IDs

### Before

```apex
@IsTest
private class CaseRouterTest {
    @IsTest
    static void high_goes_to_tier2() {
        Case c = new Case(Priority = 'High', OwnerId = '00G3x000003efgH');
        // ...
    }
}
```

### After

```apex
@IsTest
private class CaseRouterTest {
    @IsTest
    static void high_goes_to_tier2() {
        Group tier2 = new Group(Name = 'Tier 2', DeveloperName = 'Tier2_Queue', Type = 'Queue');
        insert tier2;
        QueueSObject qs = new QueueSObject(QueueId = tier2.Id, SObjectType = 'Case');
        insert qs;

        Case c = new Case(Priority = 'High');
        insert c;
        Test.startTest();
        CaseRouter.route(new List<Case>{ c });
        Test.stopTest();

        Case reloaded = [SELECT OwnerId FROM Case WHERE Id = :c.Id];
        System.assertEquals(tier2.Id, reloaded.OwnerId);
    }
}
```

The test creates its own data and captures IDs at runtime. Runs in any org.
