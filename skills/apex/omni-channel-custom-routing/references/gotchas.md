# Gotchas — Omni-Channel Custom Routing

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: IsReadyForRouting Must Be False on Insert

**What happens:** If `IsReadyForRouting = true` is set during the initial `PendingServiceRouting` insert — before any `SkillRequirement` records exist — the routing engine immediately evaluates the work item against an empty skill list. Depending on org configuration, one of two things occurs: the work item routes to any available agent (ignoring skill matching entirely), or the platform throws a DML exception referencing missing routing requirements.

**When it occurs:** Any time the three-DML sequence is collapsed into one or two steps. Most commonly seen when developers copy examples that omit the intermediate `IsReadyForRouting = false` state, or when they test with a single-record helper method that "works" because no agents are online (so routing never fires during the insert).

**How to avoid:** Always insert `PendingServiceRouting` with `IsReadyForRouting = false`. Insert all `SkillRequirement` child records. Only then update `IsReadyForRouting` to `true`. Treat these as three separate, mandatory DML operations.

---

## Gotcha 2: Hardcoded ServiceChannelId Breaks on Sandbox Refresh

**What happens:** `ServiceChannel.Id` is an org-specific record Id that is reassigned when a sandbox is refreshed from production. Apex that embeds a hardcoded `ServiceChannelId` string literal compiles and deploys without error, but at runtime the `PendingServiceRouting` insert either inserts against a non-existent channel (which may succeed silently but produces no routing) or throws a FIELD_INTEGRITY_EXCEPTION referencing an invalid Id.

**When it occurs:** Any deployment from production to a freshly refreshed sandbox, or promotion from one sandbox tier to another. The bug is invisible during development in a stable sandbox but manifests immediately after any environment refresh.

**How to avoid:** Always query `ServiceChannel` by `DeveloperName` at runtime:
```apex
ServiceChannel sc = [
    SELECT Id FROM ServiceChannel WHERE DeveloperName = 'Cases' LIMIT 1
];
Id channelId = sc.Id;
```
For high-frequency code paths, cache the result in a custom metadata type or Platform Cache rather than hardcoding the Id.

---

## Gotcha 3: Orphaned PendingServiceRouting Blocks Re-Routing

**What happens:** A work item can have at most one active `PendingServiceRouting` record at a time. If Apex inserts a `PendingServiceRouting` record but an exception prevents the subsequent `SkillRequirement` insert or the `IsReadyForRouting` update, the orphaned record remains in the database. Any future attempt to route the same work item fails with a DUPLICATE_VALUE error on `WorkItemId`.

**When it occurs:** Any unhandled exception after the first DML insert in the three-step sequence. Common causes: validation rule failures on `SkillRequirement`, CPU/DML governor limit hits in a large transaction, or platform errors during the flag-flip update.

**How to avoid:** Wrap the entire three-DML sequence in a `try/catch`. In the `catch` block, delete any `PendingServiceRouting` records that were successfully inserted before the failure:
```apex
try {
    insert psrList;
    insert srList;
    update psrList; // flip flag
} catch (Exception ex) {
    if (!psrList.isEmpty() && psrList[0].Id != null) {
        delete psrList; // clean up orphans
    }
    throw ex; // re-throw or log
}
```

---

## Gotcha 4: SOQL on Skill Inside the Routing Loop Hits Governor Limits

**What happens:** When routing a batch of work items, querying `Skill` by `DeveloperName` inside the per-record loop issues one synchronous SOQL query per work item. In a trigger processing 150 Cases, this produces 150 SOQL queries — well over the 100-query synchronous limit — causing a System.LimitException.

**When it occurs:** Any Apex routing logic that retrieves `Skill` or `ServiceChannel` records inside a `for` loop over the work items list. Often introduced when single-record prototypes are extended to handle bulk transactions.

**How to avoid:** Collect all required `DeveloperName` values before the loop, issue a single bulk `SELECT` with an `IN` clause, and build a `Map<String, Id>` for O(1) lookup inside the loop.

---

## Gotcha 5: Deleting PendingServiceRouting Does Not Unassign an Already-Routed Work Item

**What happens:** If a `PendingServiceRouting` record is deleted after `IsReadyForRouting` has been set to `true` and the routing engine has already assigned the work item to an agent, deleting the `PendingServiceRouting` record does not retract the assignment from the agent's Omni-Channel queue. The deletion only removes the routing ticket — the `OwnerId` on the work item remains pointed at the agent.

**When it occurs:** Cleanup logic that assumes deleting the `PendingServiceRouting` record will "cancel" the routing and return the work item to an unassigned state. This is a common misconception when building cancellation or re-routing flows.

**How to avoid:** If re-routing is needed after a work item has already been assigned, update `OwnerId` on the work item directly (or use the Omni-Channel API) before inserting a new `PendingServiceRouting` record. Deleting the old routing ticket is correct for orphan cleanup, not for mid-flight cancellation.
