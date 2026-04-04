# Apex Managed Sharing — Work Template

Use this template when implementing or reviewing Apex managed sharing for a custom or standard object.

## Scope

**Skill:** `apex-managed-sharing`

**Request summary:** (fill in what the user asked for — e.g., "Grant Edit access to Project__c records for users in matching territory assignments")

## Context Gathered

Answer these before writing any code:

- **Object and OWD:** What object needs programmatic sharing? What is its current OWD (Private / Public Read Only / Public Read/Write)? Apex sharing has no effect on Public Read/Write objects.
- **Share object name:** `<ObjectAPIName>__Share` (custom) or `<StandardObject>Share` (standard, e.g., `OpportunityShare`)
- **Row cause:** Will you use a custom Apex sharing reason (recommended for custom objects) or `Manual` (standard objects only)? If custom, confirm the reason exists in Setup before deployment.
- **Trigger or batch:** Is this a real-time grant on a related-record DML event (trigger), a full recalculation across all records (batch), or both?
- **Volume estimate:** How many parent records? How many share rows per record? Confirm total DML rows per transaction stays under 10,000.

## Apex Sharing Reason Setup (if custom row cause)

- Object: ____________________
- Sharing Reason Label: ____________________
- Sharing Reason API Name: ____________________`__c`
- Full RowCause reference in Apex: `<ObjectAPIName>__Share.rowCause.<ReasonName>__c`
- Recalculation class to register: ____________________

## Share Object Fields

| Field | Value |
|---|---|
| `ParentId` | ID of the record being shared |
| `UserOrGroupId` | ID of the User, Role, or Public Group |
| `AccessLevel` | `Read` or `Edit` (not `All`) |
| `RowCause` | `<ObjectAPIName>__Share.rowCause.<ReasonName>__c` or `'Manual'` |

## Trigger Handler Pattern (for event-driven sharing)

```apex
public without sharing class <Object>ShareHandler {

    public static void grantAccess(List<TriggeringObject__c> newRecords) {
        Set<Id> parentIds = new Set<Id>();
        for (TriggeringObject__c rec : newRecords) {
            parentIds.add(rec.<ParentLookupField__c>);
        }

        // Query existing grants to prevent DUPLICATE_VALUE
        Set<String> existingKeys = new Set<String>();
        for (<Object>__Share s : [
            SELECT ParentId, UserOrGroupId
            FROM <Object>__Share
            WHERE ParentId IN :parentIds
            AND RowCause = :<Object>__Share.rowCause.<ReasonName>__c
        ]) {
            existingKeys.add(s.ParentId + '_' + s.UserOrGroupId);
        }

        List<<Object>__Share> toInsert = new List<<Object>__Share>();
        for (TriggeringObject__c rec : newRecords) {
            String key = rec.<ParentLookupField__c> + '_' + rec.<UserField__c>;
            if (!existingKeys.contains(key)) {
                toInsert.add(new <Object>__Share(
                    ParentId      = rec.<ParentLookupField__c>,
                    UserOrGroupId = rec.<UserField__c>,
                    AccessLevel   = 'Edit',   // or 'Read'
                    RowCause      = <Object>__Share.rowCause.<ReasonName>__c
                ));
            }
        }

        if (!toInsert.isEmpty()) {
            Database.insert(toInsert, false); // false = partial success allowed
        }
    }

    public static void revokeAccess(List<TriggeringObject__c> oldRecords) {
        Set<Id> parentIds = new Set<Id>();
        Set<Id> userIds   = new Set<Id>();
        for (TriggeringObject__c rec : oldRecords) {
            parentIds.add(rec.<ParentLookupField__c>);
            userIds.add(rec.<UserField__c>);
        }

        List<<Object>__Share> toDelete = [
            SELECT Id FROM <Object>__Share
            WHERE ParentId IN :parentIds
            AND UserOrGroupId IN :userIds
            AND RowCause = :<Object>__Share.rowCause.<ReasonName>__c
        ];
        if (!toDelete.isEmpty()) {
            delete toDelete;
        }
    }
}
```

## Recalculation Batch Pattern

```apex
global without sharing class <Object>ShareRecalculationBatch
    implements Database.Batchable<SObject> {

    global Database.QueryLocator start(Database.BatchableContext bc) {
        return Database.getQueryLocator('SELECT Id FROM <Object>__c');
    }

    global void execute(Database.BatchableContext bc, List<<Object>__c> scope) {
        Set<Id> parentIds = new Map<Id, <Object>__c>(scope).keySet();

        // Delete stale shares for this row cause and batch
        delete [
            SELECT Id FROM <Object>__Share
            WHERE ParentId IN :parentIds
            AND RowCause = :<Object>__Share.rowCause.<ReasonName>__c
        ];

        // Recompute access grants
        List<<RelatedObject>__c> assignments = [
            SELECT <ParentField__c>, <UserField__c>
            FROM <RelatedObject>__c
            WHERE <ParentField__c> IN :parentIds
            AND <UserField__c> != null
        ];

        Map<String, <Object>__Share> shareMap = new Map<String, <Object>__Share>();
        for (<RelatedObject>__c a : assignments) {
            String key = a.<ParentField__c> + '_' + a.<UserField__c>;
            if (!shareMap.containsKey(key)) {
                shareMap.put(key, new <Object>__Share(
                    ParentId      = a.<ParentField__c>,
                    UserOrGroupId = a.<UserField__c>,
                    AccessLevel   = 'Edit',
                    RowCause      = <Object>__Share.rowCause.<ReasonName>__c
                ));
            }
        }

        if (!shareMap.isEmpty()) {
            Database.insert(shareMap.values(), false);
        }
    }

    global void finish(Database.BatchableContext bc) {
        // Optional: notify admin or trigger follow-on job
    }
}
```

**Invoke:**

```apex
Database.executeBatch(new <Object>ShareRecalculationBatch(), 200);
```

## Checklist

- [ ] OWD for the object is Private or Public Read Only (Apex sharing has no effect on Public Read/Write)
- [ ] Apex sharing reason created in Setup before this code is deployed to target org
- [ ] Recalculation batch class registered on the sharing reason in Setup
- [ ] `without sharing` declared on the recalculation batch class
- [ ] Share inserts use `Database.insert(list, false)` and log non-DUPLICATE_VALUE errors
- [ ] Stale shares deleted before fresh insert in recalculation (not upsert)
- [ ] DML row count confirmed below 10,000 per transaction (trigger) and per execute (batch)
- [ ] AccessLevel is `Read` or `Edit` — not `All`

## Notes

(Record any deviations from the standard pattern and why.)
