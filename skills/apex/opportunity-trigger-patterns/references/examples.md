# Examples — Opportunity Trigger Patterns

## Example 1: Stage-Change Detection With Mixed Batch

**Context:** An Opportunity trigger handler must create a follow-up Task when an Opportunity moves to `Closed Lost`, but a data load sends 200 Opportunity updates at once — some changing stage, most not.

**Problem:** Without filtering by stage change, the handler processes all 200 records even when only 3 changed stage. Worse, checking `opp.StageName == 'Closed Lost'` without comparing to `Trigger.oldMap` creates a duplicate Task every time the record is saved, even with no stage change.

**Solution:**

```apex
public class OpportunityTriggerHandler {

    public void onAfterUpdate(List<Opportunity> newList, Map<Id, Opportunity> oldMap) {
        List<Task> tasksToInsert = new List<Task>();

        for (Opportunity opp : newList) {
            Opportunity old = oldMap.get(opp.Id);

            // Only act when stage transitions INTO Closed Lost
            Boolean justClosedLost = opp.StageName == 'Closed Lost'
                && old.StageName != 'Closed Lost';

            if (justClosedLost) {
                tasksToInsert.add(new Task(
                    WhatId      = opp.Id,
                    Subject     = 'Closed Lost — Schedule Debrief',
                    ActivityDate = Date.today().addDays(7),
                    OwnerId     = opp.OwnerId,
                    Status      = 'Not Started',
                    Priority    = 'Normal'
                ));
            }
        }

        if (!tasksToInsert.isEmpty()) {
            insert tasksToInsert;
        }
    }
}
```

**Why it works:** The dual condition `opp.StageName == 'Closed Lost' && old.StageName != 'Closed Lost'` detects a transition rather than a state. Records already in Closed Lost before this update are skipped. The collected list is inserted once after the loop, keeping DML count to 1 regardless of batch size.

---

## Example 2: Bulkified Open Pipeline Rollup to Account

**Context:** An Account record needs to display `Open_Pipeline__c` — the sum of `Amount` for all open (non-closed) Opportunities. This must stay current when Opportunities are inserted, updated, or deleted, and must handle Opportunity reparenting (AccountId change).

**Problem:** A naive implementation queries Opportunities for each Account inside a loop, hitting the 101-SOQL governor limit on any batch larger than 100 records. A version that ignores `Trigger.oldMap.AccountId` leaves stale totals on former parent Accounts when reparenting occurs.

**Solution:**

```apex
public class OpportunityTriggerHandler {

    public void rollupOpenPipelineToAccount(
        List<Opportunity> newList,
        Map<Id, Opportunity> oldMap
    ) {
        Set<Id> accountIds = new Set<Id>();

        for (Opportunity opp : newList) {
            if (opp.AccountId != null) accountIds.add(opp.AccountId);
        }
        // Capture old AccountIds to handle reparenting and deletes
        if (oldMap != null) {
            for (Opportunity old : oldMap.values()) {
                if (old.AccountId != null) accountIds.add(old.AccountId);
            }
        }

        if (accountIds.isEmpty()) return;

        // One aggregate query — grouped by AccountId
        Map<Id, Decimal> pipelineByAccount = new Map<Id, Decimal>();
        for (AggregateResult ar : [
            SELECT AccountId acctId, SUM(Amount) total
            FROM Opportunity
            WHERE AccountId IN :accountIds
              AND IsClosed = false
            GROUP BY AccountId
        ]) {
            pipelineByAccount.put(
                (Id) ar.get('acctId'),
                (Decimal) ar.get('total')
            );
        }

        // Build update list — zero out accounts with no open opps
        List<Account> toUpdate = new List<Account>();
        for (Id acctId : accountIds) {
            toUpdate.add(new Account(
                Id = acctId,
                Open_Pipeline__c = pipelineByAccount.containsKey(acctId)
                    ? pipelineByAccount.get(acctId)
                    : 0
            ));
        }

        update toUpdate; // One DML statement
    }
}
```

**Test wire-up** — register this on `after insert, after update, after delete, after undelete`:

```apex
trigger OpportunityTrigger on Opportunity (
    after insert, after update, after delete, after undelete
) {
    if (!TriggerControl.isActive('Opportunity')) return;
    OpportunityTriggerHandler handler = new OpportunityTriggerHandler();
    List<Opportunity> records = Trigger.isDelete ? Trigger.old : Trigger.new;
    Map<Id, Opportunity> oldMap = Trigger.isDelete ? null : Trigger.oldMap;
    handler.rollupOpenPipelineToAccount(records, oldMap);
}
```

**Why it works:** All affected Account IDs are collected in one pass before any SOQL. The aggregate query returns exactly one row per Account regardless of how many Opportunities it has. The old AccountId set handles reparenting. Total SOQL: 1. Total DML: 1.

---

## Example 3: Revenue Split Redistribution After Team Member Add

**Context:** Opportunity Splits are enabled. When a new `OpportunityTeamMember` is added, the Revenue split percentages should be redistributed equally across all current team members. The constraint: percentages must sum to exactly 100 for Revenue split types.

**Problem:** Integer division with `N` members produces a remainder when 100 is not evenly divisible by N (e.g. 3 members gives 33 + 33 + 33 = 99, not 100). A naive implementation leaves a 1% gap and the entire upsert fails with `DmlException: FIELD_INTEGRITY_EXCEPTION`.

**Solution:**

```apex
public class OpportunityTeamMemberTriggerHandler {

    private static final String REVENUE_SPLIT_TYPE_NAME = 'Revenue';

    private static Id getRevenueSplitTypeId() {
        List<OpportunitySplitType> types = [
            SELECT Id FROM OpportunitySplitType
            WHERE MasterLabel = :REVENUE_SPLIT_TYPE_NAME
            LIMIT 1
        ];
        return types.isEmpty() ? null : types[0].Id;
    }

    public void onAfterInsert(List<OpportunityTeamMember> newMembers) {
        Id splitTypeId = getRevenueSplitTypeId();
        if (splitTypeId == null) return;

        Set<Id> oppIds = new Set<Id>();
        for (OpportunityTeamMember otm : newMembers) oppIds.add(otm.OpportunityId);

        Map<Id, List<Id>> memberUsersByOpp = new Map<Id, List<Id>>();
        for (OpportunityTeamMember otm : [
            SELECT UserId, OpportunityId
            FROM OpportunityTeamMember
            WHERE OpportunityId IN :oppIds
            ORDER BY CreatedDate ASC
        ]) {
            if (!memberUsersByOpp.containsKey(otm.OpportunityId)) {
                memberUsersByOpp.put(otm.OpportunityId, new List<Id>());
            }
            memberUsersByOpp.get(otm.OpportunityId).add(otm.UserId);
        }

        List<OpportunitySplit> splitsToUpsert = new List<OpportunitySplit>();
        for (Id oppId : memberUsersByOpp.keySet()) {
            List<Id> users = memberUsersByOpp.get(oppId);
            Integer count = users.size();
            Integer baseShare = 100 / count;
            Integer remainder = 100 - (baseShare * count);

            for (Integer i = 0; i < count; i++) {
                Integer share = (i == 0) ? baseShare + remainder : baseShare;
                splitsToUpsert.add(new OpportunitySplit(
                    OpportunityId   = oppId,
                    SplitOwnerId    = users[i],
                    SplitPercentage = share,
                    SplitTypeId     = splitTypeId
                ));
            }
        }

        if (!splitsToUpsert.isEmpty()) {
            upsert splitsToUpsert;
        }
    }
}
```

**Why it works:** The remainder is computed explicitly and assigned to one record, guaranteeing the sum equals exactly 100. The upsert uses the composite natural key so re-running on the same Opportunity updates existing splits rather than inserting duplicates.

---

## Anti-Pattern: Querying Opportunities Inside an Account Rollup Loop

**What practitioners do:** Write a `for (Opportunity opp : newList)` loop that includes a SOQL query inside — e.g. `[SELECT SUM(Amount) FROM Opportunity WHERE AccountId = :opp.AccountId AND IsClosed = false]`.

**What goes wrong:** Each iteration consumes one SOQL query from the governor limit of 100. A batch of 102 Opportunities from two Accounts hits the limit at record 101, crashing the transaction with `System.LimitException: Too many SOQL queries: 101`.

**Correct approach:** Collect all unique AccountIds before the loop in a `Set<Id>`, run one aggregate SOQL grouped by AccountId, load results into a `Map<Id, Decimal>`, then read from the map inside the loop. Zero SOQL inside loops.
