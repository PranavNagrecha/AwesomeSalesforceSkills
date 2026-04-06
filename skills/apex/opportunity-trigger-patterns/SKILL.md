---
name: opportunity-trigger-patterns
description: "Use when building or reviewing Apex triggers on the Opportunity object — stage-change detection, amount rollups to Account, OpportunityTeamMember sync, or OpportunitySplit calculations. Trigger keywords: stage change automation, opportunity rollup, team member sync, split percentage, Trigger.oldMap stage comparison. NOT for generic trigger framework structure (use apex/trigger-framework) and NOT for Flow-based opportunity automation (use admin/flow-for-admins)."
category: apex
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Performance
  - Scalability
triggers:
  - "Opportunity stage change trigger not firing correctly or firing on every save"
  - "How do I detect when an Opportunity moves to Closed Won in Apex"
  - "Rollup Opportunity amounts to parent Account in a trigger"
  - "OpportunitySplit DML error in trigger context"
  - "Opportunity team member sync with split percentage rebalancing"
tags:
  - opportunity
  - trigger
  - stage-change
  - rollup
  - opportunity-splits
  - team-members
  - bulkification
inputs:
  - "Org edition and whether Opportunity Splits and Team Members are enabled"
  - "Existing trigger framework constraints (one trigger per object rule)"
  - "Whether split types in the org are Revenue, Overlay, or custom"
  - "Account rollup fields or roll-up summary definitions already in place"
outputs:
  - "Bulkified Apex trigger and handler for Opportunity with stage-change, rollup, or split logic"
  - "Review findings for existing Opportunity trigger handlers"
  - "Decision guidance on before vs. after context placement for each automation type"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-06
---

# Opportunity Trigger Patterns

Use this skill when writing, reviewing, or troubleshooting Apex triggers on the Opportunity object. It covers the three highest-risk automation areas specific to Opportunity: stage-change detection with `Trigger.oldMap`, cascading rollups to the parent Account, and team member / split synchronisation.

---

## Before Starting

Gather this context before working on anything in this domain:

- Is the org using a shared trigger framework (e.g. FFLIB, Kevin O'Hara)? If yes, all Opportunity logic must be implemented inside that framework's handler, not in a standalone trigger class.
- Are **Opportunity Splits** enabled? (`Setup > Opportunity Settings > Enable Opportunity Splits`). If enabled, confirm which split types exist and which are Revenue type (the ones where percentages must sum to 100).
- Are **Opportunity Teams** enabled and are there custom team roles in use? Team member removal cascade-deletes all split records for that user — factor this into any cleanup logic.
- Does the org use roll-up summary fields from Account to Opportunity? If yes, introducing additional DML-based rollups on the same records risks conflicting with platform-managed roll-ups and can cause lock contention.
- What is the maximum batch size expected in data loads? Rollup and split logic must be bulkified for 200-record batches.

---

## Core Concepts

### Stage-Change Detection with Trigger.oldMap

The most reliable way to detect an Opportunity stage change is to compare `Trigger.new` against `Trigger.oldMap` in an after-update context. Before-update is acceptable for field defaulting on the record itself (e.g. setting `CloseDate` when moving to Closed Won) but after-update is required for any DML on related objects (e.g. creating a Task, firing a Platform Event, or updating Account).

```apex
for (Opportunity opp : Trigger.new) {
    Opportunity old = Trigger.oldMap.get(opp.Id);
    if (opp.StageName != old.StageName) {
        // stage changed — safe to act in after-update
    }
}
```

`Trigger.oldMap` is only populated on update and delete operations. It is `null` on insert — always guard for insert context before accessing it.

### Cascading Rollups to Account

Rollup patterns that aggregate Opportunity totals onto the parent Account (e.g. total open pipeline, weighted forecast amount) must:

1. Collect the unique set of `AccountId` values from `Trigger.new` and `Trigger.oldMap` in a single pass.
2. Issue **one aggregate SOQL** query against Opportunity grouped by AccountId — never loop-query inside trigger execution.
3. Issue **one DML** update on the collected Account records.

The trigger context includes both inserted, updated, and deleted records when a rollup listens to after-delete and after-undelete. Register the trigger for all four events (`after insert, after update, after delete, after undelete`) to keep the rollup consistent.

### OpportunitySplit DML Constraints

`OpportunitySplit` records are child records of Opportunity. The platform enforces the following constraints that Apex cannot override:

- **DML on `OpportunitySplit` is not supported in before-trigger contexts.** Any insert, update, or delete of split records must occur in an `after insert` or `after update` handler.
- For **Revenue split types**, the sum of `SplitPercentage` across all split records for one Opportunity must equal 100. Inserting or updating splits that break this constraint causes a `DmlException` even inside a test.
- For **Overlay split types**, percentages are unconstrained — they can exceed 100 or sit at zero individually.
- Deleting an `OpportunityTeamMember` record **cascade-deletes** all `OpportunitySplit` records for that user on that Opportunity. Triggers that recreate team members or rebalance splits must account for this ordering.

### OpportunityTeamMember Sync

`OpportunityTeamMember` records are not directly writable by most non-owner users. The primary constraint: only the Opportunity owner or a user with "Manage Opportunity Team Members" permission can insert or delete team member records. Triggers that run as the Opportunity's owner's context must be reviewed for sharing implications. `with sharing` in the handler class will apply the running user's sharing rules to SOQL but does not change DML capability for team member records — test this explicitly in a multi-user test.

---

## Common Patterns

### Pattern 1: Stage-Change Action With After-Update Guard

**When to use:** Any time a business process must fire when an Opportunity moves to a specific stage (e.g. Closed Won creates an Order, Closed Lost schedules a follow-up Task, Prospecting to Qualification sends a notification).

**How it works:**

1. Register the trigger on `after update`.
2. In the handler, iterate `Trigger.new`. For each record, look up `Trigger.oldMap.get(opp.Id)` to get the previous stage.
3. Collect records where stage changed into a `List<Opportunity>` to avoid processing unchanged records.
4. Perform all related-record DML once, outside the loop.

```apex
public void onAfterUpdate(List<Opportunity> newList, Map<Id, Opportunity> oldMap) {
    List<Task> tasksToInsert = new List<Task>();

    for (Opportunity opp : newList) {
        String oldStage = oldMap.get(opp.Id).StageName;
        if (opp.StageName == 'Closed Lost' && oldStage != 'Closed Lost') {
            tasksToInsert.add(new Task(
                WhatId = opp.Id,
                Subject = 'Closed Lost Follow-up',
                ActivityDate = Date.today().addDays(7),
                OwnerId = opp.OwnerId
            ));
        }
    }

    if (!tasksToInsert.isEmpty()) {
        insert tasksToInsert;
    }
}
```

**Why not the alternative:** Using before-update for related-record DML fails at runtime (`DML not allowed in before trigger`). Using a separate scheduled job to detect stage changes creates lag and misses same-day multi-stage progressions.

### Pattern 2: Bulkified Account Rollup

**When to use:** When platform roll-up summary fields are insufficient (e.g. the rollup must span object hierarchies, include filter conditions not supported by ROLLUP fields, or update a field on Account that depends on multiple Opportunity stages simultaneously).

**How it works:**

1. Collect all parent `AccountId` values from both `Trigger.new` and `Trigger.oldMap` (to handle reparenting).
2. Run one aggregate SOQL to compute the rollup values.
3. Build a `Map<Id, Account>` of updates and issue one `update` call.

```apex
public void onAfterUpdate(List<Opportunity> newList, Map<Id, Opportunity> oldMap) {
    Set<Id> accountIds = new Set<Id>();
    for (Opportunity opp : newList) {
        if (opp.AccountId != null) accountIds.add(opp.AccountId);
        Opportunity old = oldMap.get(opp.Id);
        if (old.AccountId != null) accountIds.add(old.AccountId); // handle reparent
    }

    Map<Id, AggregateResult> rollupMap = new Map<Id, AggregateResult>();
    for (AggregateResult ar : [
        SELECT AccountId acctId, SUM(Amount) totalPipeline
        FROM Opportunity
        WHERE AccountId IN :accountIds
          AND IsClosed = false
        GROUP BY AccountId
    ]) {
        rollupMap.put((Id) ar.get('acctId'), ar);
    }

    List<Account> accountsToUpdate = new List<Account>();
    for (Id acctId : accountIds) {
        Decimal total = rollupMap.containsKey(acctId)
            ? (Decimal) rollupMap.get(acctId).get('totalPipeline')
            : 0;
        accountsToUpdate.add(new Account(Id = acctId, Open_Pipeline__c = total));
    }

    if (!accountsToUpdate.isEmpty()) {
        update accountsToUpdate;
    }
}
```

**Why not the alternative:** Querying inside a loop causes `System.LimitException: Too many SOQL queries` at 101+ queries. Using a platform Roll-Up Summary field cannot perform conditional aggregation across multiple Stage values.

### Pattern 3: OpportunitySplit Rebalancing After Team Member Add

**When to use:** When adding an `OpportunityTeamMember` automatically triggers an equal redistribution of Revenue split percentages across the full team.

**How it works:**

1. Register a trigger on `OpportunityTeamMember` for `after insert`.
2. Query the full set of active team members for the affected Opportunity.
3. In an `after insert` context (DML on splits is allowed here), query existing splits, compute equal shares, and upsert using `OpportunitySplit`.
4. Ensure percentages sum to exactly 100 before DML to avoid a constraint violation. Use integer division with the remainder assigned to the first record.

```apex
// After-insert handler on OpportunityTeamMember
public void onAfterInsert(List<OpportunityTeamMember> newMembers) {
    Set<Id> oppIds = new Set<Id>();
    for (OpportunityTeamMember otm : newMembers) oppIds.add(otm.OpportunityId);

    Map<Id, List<OpportunityTeamMember>> membersByOpp = new Map<Id, List<OpportunityTeamMember>>();
    for (OpportunityTeamMember otm : [
        SELECT Id, UserId, OpportunityId
        FROM OpportunityTeamMember
        WHERE OpportunityId IN :oppIds
    ]) {
        if (!membersByOpp.containsKey(otm.OpportunityId)) {
            membersByOpp.put(otm.OpportunityId, new List<OpportunityTeamMember>());
        }
        membersByOpp.get(otm.OpportunityId).add(otm);
    }

    List<OpportunitySplit> splitsToUpsert = new List<OpportunitySplit>();
    for (Id oppId : membersByOpp.keySet()) {
        List<OpportunityTeamMember> members = membersByOpp.get(oppId);
        Integer count = members.size();
        Integer baseShare = 100 / count;
        Integer remainder = 100 - (baseShare * count);

        for (Integer i = 0; i < count; i++) {
            Integer share = (i == 0) ? baseShare + remainder : baseShare;
            splitsToUpsert.add(new OpportunitySplit(
                OpportunityId = oppId,
                SplitOwnerId = members[i].UserId,
                SplitPercentage = share,
                SplitTypeId = RevenueSplitTypeId // resolved from Custom Metadata
            ));
        }
    }

    if (!splitsToUpsert.isEmpty()) upsert splitsToUpsert;
}
```

**Why not the alternative:** Attempting this in a before-insert trigger on `OpportunityTeamMember` throws a DML restriction. Relying on a Flow to handle this logic creates an automation coexistence risk and depends on the order of execution between Flow and trigger.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Field update on Opportunity itself when stage changes | before-update handler | Before-save field mutations are cheaper and do not require DML |
| Creating related records on stage change | after-update handler | DML on related objects is not allowed in before contexts |
| Rolling up Opportunity amounts to Account | after insert/update/delete/undelete handler | All four events affect aggregate totals; before contexts cannot issue DML on Account |
| Redistributing Revenue splits after team add | after-insert on OpportunityTeamMember | DML on OpportunitySplit is blocked in before contexts |
| Overlay split percentages need rebalancing | after-update on Opportunity | Overlay types have no 100% constraint — update freely in after context |
| Stage-change logic that also calls an external API | after-update, enqueue a Queueable | Callouts are not allowed in synchronous trigger execution |
| Detecting if a team member was removed | after-delete on OpportunityTeamMember | Cascade-delete of splits has already occurred by after-delete; no need to manually delete splits |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Confirm org configuration** — check whether Opportunity Splits and Teams are enabled, identify the split types in use (Revenue vs Overlay), and confirm whether an existing trigger framework handles dispatch.
2. **Identify automation scope** — determine which of the three high-risk areas apply: stage-change detection, Account rollup, or team member / split sync. Each has different trigger event requirements and DML constraints.
3. **Choose trigger context** — use the Decision Guidance table above to select the correct before/after context for each piece of logic. Placing DML on related records in a before context causes an immediate runtime failure.
4. **Implement with bulkification** — collect all affected record IDs before issuing any SOQL. Issue exactly one query and one DML statement per related object type per transaction. Never query or DML inside a loop.
5. **Handle split percentage arithmetic** — when redistributing Revenue splits, compute integer shares, assign the remainder to one record, and verify the sum equals exactly 100 before issuing DML. A single split percentage mismatch causes the entire DML to fail.
6. **Write multi-record and edge-case tests** — test with 200-record bulk batches, test stage-change with no-stage-change mixed batches, test insert of team members when no prior splits exist, and test reparenting (AccountId change) for rollup logic.
7. **Run the checker script and validate** — execute `python3 scripts/check_opportunity_trigger_patterns.py --manifest-dir <metadata_root>` then run `python3 scripts/validate_repo.py` before marking work complete.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] `Trigger.oldMap` is only accessed in update/delete contexts — never in insert
- [ ] No SOQL queries or DML statements inside loops
- [ ] Revenue split percentages verified to sum to 100 before DML
- [ ] OpportunitySplit DML placed in after-insert or after-update only, never before
- [ ] Account rollup collects AccountIds from both old and new maps to handle reparenting
- [ ] Stage-change detection explicitly compares old.StageName != new.StageName
- [ ] Trigger framework activation bypass guard present and tested
- [ ] Test class covers 200-record batch, stage-change-only subset, and no-change-subset

---

## Salesforce-Specific Gotchas

1. **OpportunitySplit DML is blocked in before contexts** — Attempting to insert, update, or delete `OpportunitySplit` records inside any before-trigger (including before insert on OpportunityTeamMember) results in a runtime `System.DmlException`. Move all split DML to an after context.
2. **Team member deletion cascade-deletes splits** — When an `OpportunityTeamMember` record is deleted, all `OpportunitySplit` records for that user on that Opportunity are automatically removed by the platform before after-delete fires. Any re-creation logic must run in after-delete and must not attempt to delete splits first (they are already gone).
3. **Revenue split percentages must sum to 100** — The platform enforces this constraint at the database level for Revenue split types. Integer arithmetic with multiple team members creates rounding remainders. Assign the remainder explicitly to one record or the DML will fail even in tests.
4. **`Trigger.oldMap` is null on insert** — Any handler method that checks `oldMap.get(opp.Id)` without first guarding for insert context throws a `NullPointerException` on bulk insert. Always check `Trigger.isInsert` before accessing `oldMap`.
5. **Reparenting breaks account rollups** — If an Opportunity's `AccountId` is changed in an update, the old parent Account no longer receives a rollup update unless the trigger explicitly adds `Trigger.oldMap` AccountId values to the aggregation set. Rollup logic that only reads `Trigger.new.AccountId` silently leaves stale totals on the former parent.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Opportunity trigger handler | Bulkified handler class with onAfterUpdate, onAfterInsert, and context-separated methods |
| Account rollup logic | Aggregate SOQL + single DML update pattern for parent Account fields |
| Split rebalance handler | After-insert handler on OpportunityTeamMember with integer remainder distribution |
| Review findings | Structured list of trigger issues against the Review Checklist above |

---

## Related Skills

- `apex/trigger-framework` — Use for the outer trigger dispatch structure, recursion guards, and activation bypass. This skill covers only Opportunity-specific logic patterns; the framework handles the container.
- `apex/governor-limits` — Consult when rollup queries or split upserts approach the SOQL or DML governor limits in large transactions.
- `apex/callout-and-dml-transaction-boundaries` — Use when stage-change automation must call an external API; callouts from synchronous triggers require a Queueable or Platform Event boundary.
- `admin/opportunity-management` — Use for non-Apex aspects of Opportunity configuration: stage paths, probability mappings, forecast categories, and validation rules.
