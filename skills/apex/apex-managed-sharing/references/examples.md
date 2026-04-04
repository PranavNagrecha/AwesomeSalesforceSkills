# Examples — Apex Managed Sharing

## Example 1: Territory-Based Sharing for a Custom Object (Trigger)

**Context:** An org has a custom object `Project__c` with Private OWD. A junction object `Project_Territory__c` links projects to internal territory records. When a `Project_Territory__c` record is created, the territory's assigned user should receive Edit access to the project. When the junction record is deleted, the grant should be revoked.

**Problem:** Without Apex managed sharing, the territory user cannot see the project at all (Private OWD, not in the owner's role hierarchy). Declarative criteria-based sharing rules cannot model "share based on a junction record's related user field."

**Solution:**

```apex
// File: ProjectTerritoryShareHandler.cls
// Requires: Apex Sharing Reason "TerritoryAccess" created in Setup
//           on Project__c before this code is deployed.

public without sharing class ProjectTerritoryShareHandler {

    /**
     * Called from Project_Territory__c trigger on after insert.
     * Grants Edit access to the project for each territory's assigned user.
     */
    public static void grantAccess(List<Project_Territory__c> newRecords) {
        // Collect unique Project IDs to query existing shares (avoid duplicates)
        Set<Id> projectIds = new Set<Id>();
        for (Project_Territory__c pt : newRecords) {
            projectIds.add(pt.Project__c);
        }

        // Build a set of already-granted (ParentId, UserOrGroupId) pairs
        Set<String> existingKeys = new Set<String>();
        for (Project__Share existing : [
            SELECT ParentId, UserOrGroupId
            FROM Project__Share
            WHERE ParentId IN :projectIds
            AND RowCause = :Project__Share.rowCause.TerritoryAccess__c
        ]) {
            existingKeys.add(existing.ParentId + '_' + existing.UserOrGroupId);
        }

        List<Project__Share> toInsert = new List<Project__Share>();
        for (Project_Territory__c pt : newRecords) {
            String key = pt.Project__c + '_' + pt.Assigned_User__c;
            if (!existingKeys.contains(key)) {
                toInsert.add(new Project__Share(
                    ParentId       = pt.Project__c,
                    UserOrGroupId  = pt.Assigned_User__c,
                    AccessLevel    = 'Edit',
                    RowCause       = Project__Share.rowCause.TerritoryAccess__c
                ));
            }
        }

        if (!toInsert.isEmpty()) {
            // allOrNone = false: DUPLICATE_VALUE on any row does not roll back others
            Database.SaveResult[] results = Database.insert(toInsert, false);
            for (Database.SaveResult sr : results) {
                if (!sr.isSuccess()) {
                    for (Database.Error err : sr.getErrors()) {
                        // Log but do not rethrow DUPLICATE_VALUE — it means the grant
                        // already exists, which is the desired end state.
                        if (err.getStatusCode() != StatusCode.DUPLICATE_VALUE) {
                            System.debug(LoggingLevel.ERROR,
                                'Share insert error: ' + err.getMessage());
                        }
                    }
                }
            }
        }
    }

    /**
     * Called from Project_Territory__c trigger on after delete.
     * Revokes the TerritoryAccess grant for each deleted junction record.
     */
    public static void revokeAccess(List<Project_Territory__c> oldRecords) {
        Set<Id> projectIds = new Set<Id>();
        Set<Id> userIds    = new Set<Id>();
        for (Project_Territory__c pt : oldRecords) {
            projectIds.add(pt.Project__c);
            userIds.add(pt.Assigned_User__c);
        }

        List<Project__Share> toDelete = [
            SELECT Id
            FROM Project__Share
            WHERE ParentId IN :projectIds
            AND UserOrGroupId IN :userIds
            AND RowCause = :Project__Share.rowCause.TerritoryAccess__c
        ];

        if (!toDelete.isEmpty()) {
            delete toDelete;
        }
    }
}
```

**Why it works:** Using the custom row cause `TerritoryAccess__c` keeps these grants isolated from manual sharing. The `Database.insert(list, false)` pattern silently absorbs duplicate inserts (e.g., if the trigger fires twice due to retry). The revoke method queries by both `ParentId` and `UserOrGroupId` to avoid deleting unrelated share rows.

---

## Example 2: Sharing Recalculation Batch Job

**Context:** The territory assignment logic has been restructured — thousands of `Project_Territory__c` records have been reassigned. All existing `TerritoryAccess__c` share rows on `Project__c` must be deleted and rebuilt from the current state of the junction table.

**Problem:** Running this recalculation in a trigger or anonymous Apex hits the 10,000 DML row limit immediately for large orgs. A batch job processes records in configurable chunks and stays within per-execute limits.

**Solution:**

```apex
// File: ProjectShareRecalculationBatch.cls
// Register this class on the TerritoryAccess Apex Sharing Reason in Setup.
// Setup > Object Manager > Project__c > Apex Sharing Reasons > TerritoryAccess > Edit

global without sharing class ProjectShareRecalculationBatch
    implements Database.Batchable<SObject> {

    // ----------------------------------------------------------------
    // start: return all Project records — without sharing so the query
    // sees every record regardless of running user's access.
    // ----------------------------------------------------------------
    global Database.QueryLocator start(Database.BatchableContext bc) {
        return Database.getQueryLocator(
            'SELECT Id FROM Project__c'
        );
    }

    // ----------------------------------------------------------------
    // execute: for each batch of projects, delete stale shares then
    // recompute and insert fresh ones.
    // ----------------------------------------------------------------
    global void execute(Database.BatchableContext bc, List<Project__c> scope) {
        Set<Id> projectIds = new Map<Id, Project__c>(scope).keySet();

        // Step 1 — Delete all existing TerritoryAccess shares for this batch
        List<Project__Share> staleShares = [
            SELECT Id
            FROM Project__Share
            WHERE ParentId IN :projectIds
            AND RowCause = :Project__Share.rowCause.TerritoryAccess__c
        ];
        if (!staleShares.isEmpty()) {
            delete staleShares;
        }

        // Step 2 — Query current territory assignments for these projects
        List<Project_Territory__c> assignments = [
            SELECT Project__c, Assigned_User__c
            FROM Project_Territory__c
            WHERE Project__c IN :projectIds
            AND Assigned_User__c != null
        ];

        // Step 3 — Build fresh share rows (deduplicated in memory)
        Map<String, Project__Share> shareMap = new Map<String, Project__Share>();
        for (Project_Territory__c pt : assignments) {
            String key = pt.Project__c + '_' + pt.Assigned_User__c;
            if (!shareMap.containsKey(key)) {
                shareMap.put(key, new Project__Share(
                    ParentId      = pt.Project__c,
                    UserOrGroupId = pt.Assigned_User__c,
                    AccessLevel   = 'Edit',
                    RowCause      = Project__Share.rowCause.TerritoryAccess__c
                ));
            }
        }

        if (!shareMap.isEmpty()) {
            Database.insert(shareMap.values(), false);
        }
    }

    // ----------------------------------------------------------------
    // finish: optional — send an email or enqueue a follow-up job
    // ----------------------------------------------------------------
    global void finish(Database.BatchableContext bc) {
        System.debug('ProjectShareRecalculationBatch complete. BatchId: ' + bc.getJobId());
    }
}
```

**Invoking the batch:**

```apex
// Anonymous Apex or a scheduled job
Database.executeBatch(new ProjectShareRecalculationBatch(), 200);
```

**Why it works:** `without sharing` on the class ensures all `Project__c` records appear in the `start` query even if the submitting user cannot normally see them. The delete-then-insert pattern avoids `DUPLICATE_VALUE` errors. The in-memory `Map` deduplication prevents inserting two rows for the same `(project, user)` pair when a user has multiple territory assignments to the same project. Batch size 200 keeps each execute well within the 10,000 DML row limit.

---

## Anti-Pattern: Inserting Share Rows Without Checking for Duplicates

**What practitioners do:** Insert share rows directly in a trigger or loop without querying whether the grant already exists:

```apex
// ANTI-PATTERN — do not copy
insert new Project__Share(
    ParentId      = projectId,
    UserOrGroupId = userId,
    AccessLevel   = 'Edit',
    RowCause      = Project__Share.rowCause.TerritoryAccess__c
);
```

**What goes wrong:** If the trigger fires more than once for the same record pair (e.g., through retries, workflow re-evaluations, or test data setup), the insert throws `System.DmlException: DUPLICATE_VALUE` and rolls back the entire transaction. In production this causes silent data loss — the triggering record is rolled back along with the share.

**Correct approach:** Either query existing rows before inserting and skip duplicates, or use `Database.insert(list, false)` and inspect `SaveResult` errors, treating `DUPLICATE_VALUE` as a non-fatal condition. The batch recalculation pattern (Example 2) avoids this entirely by deleting first.
