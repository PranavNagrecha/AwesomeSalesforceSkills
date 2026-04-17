# Examples — Apex Managed Sharing Patterns

## Example 1: Share Opportunity with every user named on a junction object

**Context:** Deal-Team__c junction lists users who should see the Opportunity.

**Problem:** OWD is Private; there is no owner relationship; sharing rule criteria cannot reference a child object.

**Solution:**

```apex
public with sharing class DealTeamShareService {
    public static void grant(Id opptyId, Id userOrGroupId) {
        OpportunityShare s = new OpportunityShare(
            OpportunityId = opptyId,
            UserOrGroupId = userOrGroupId,
            OpportunityAccessLevel = 'Read',
            RowCause = Schema.OpportunityShare.RowCause.Deal_Team__c
        );
        Database.insert(s, false);
    }
    public static void revoke(Id opptyId, Id userOrGroupId) {
        delete [SELECT Id FROM OpportunityShare
                 WHERE OpportunityId = :opptyId AND UserOrGroupId = :userOrGroupId
                   AND RowCause = :Schema.OpportunityShare.RowCause.Deal_Team__c];
    }
}
```

**Why it works:** Uses a custom RowCause so platform recalc never removes the row; revoke filters on the same RowCause so it never deletes rows inserted by rules.


---

## Example 2: Batched recalculation after a bulk data load

**Context:** 5M junction rows inserted by ETL at night.

**Problem:** Trigger-based insertion would blow CPU limits.

**Solution:**

Disable trigger insertion during the load, then enqueue a Batch Apex that re-reads the junction and upserts __Share rows in 200-row chunks using Database.insert(shares, /*allOrNone*/ false).

**Why it works:** Bulk DML on __Share objects is the most efficient path; all-or-none false lets you log duplicates without aborting.

