---
name: fsl-offline-architecture
description: "Use this skill when designing FSL Mobile offline-first architecture: data priming strategy, priming limits, conflict resolution patterns, and sync failure handling. Trigger keywords: FSL offline priming, briefcase sync FSL, offline data limits, conflict resolution MERGE_ACCEPT_YOURS, ghost records FSL. NOT for LWC offline-and-mobile (generic LWC offline, covered by lwc/lwc-offline-and-mobile), standard Salesforce Mobile App offline, or Experience Cloud offline."
category: architect
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Performance
  - Security
triggers:
  - "How does FSL Mobile offline priming work and what are the data limits"
  - "Conflict resolution strategy when FSL technician syncs after working offline"
  - "Ghost records persisting after server deletion during FSL offline session"
  - "FSL offline priming hierarchy — what data gets primed for each technician"
  - "Offline validation rules and triggers do not fire — fire at sync instead"
tags:
  - fsl
  - field-service
  - offline
  - mobile
  - priming
  - sync
  - fsl-offline-architecture
inputs:
  - "Expected number of parent Work Orders and child records per technician's daily schedule"
  - "Conflict resolution preference (local wins vs. conflict fail)"
  - "Whether technicians work in areas with intermittent connectivity"
outputs:
  - "Priming hierarchy design and record volume recommendations"
  - "Conflict resolution strategy recommendation"
  - "Ghost record cleanup plan"
  - "Data model constraints for offline-compatible FSL implementations"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-10
---

# FSL Offline Architecture

This skill activates when an architect needs to design the offline data strategy for FSL Mobile: how records are primed to the device before the work day, how conflicts are resolved when technicians sync after working offline, and how to handle FSL-specific offline constraints. FSL's offline model has hard limits, specific priming hierarchy, and conflict resolution behaviors that differ from generic Salesforce offline patterns.

---

## Before Starting

Gather this context before working on anything in this domain:

- Determine the expected number of parent Work Orders per technician per day and their child record depth (WOLI, Assets, Product). This drives priming volume calculation against the hard limits.
- Decide on conflict resolution strategy before go-live: MERGE_ACCEPT_YOURS (local device wins — default) or MERGE_FAIL_IF_CONFLICT (force manual resolution). This is a design decision, not a configuration option that can be changed post-deployment without impact.
- Understand connectivity patterns for the target deployment. Intermittent connectivity (cell coverage gaps, basements, industrial sites) drives the design toward larger priming windows and more aggressive prefetch.
- Confirm whether server-side automation (Apex triggers, validation rules) needs to fire at job completion or can be deferred to sync time.

---

## Core Concepts

### FSL Offline Priming Hierarchy

FSL Mobile primes (downloads) records to the device before the work day in a specific hierarchy:

```
ServiceResource (the technician)
  └── ServiceAppointments (today's schedule + near-future)
        └── WorkOrders
              └── WorkOrderLineItems
              └── Assets (if linked)
              └── Related records (custom objects with lookups)
```

The priming engine traverses this hierarchy automatically. Records outside this hierarchy are not primed unless explicitly configured.

**Hard limits:**
- **1,000 page references** — Each related object traversal counts as a page reference. Exceeding 1,000 causes silent failure (not an error) — records beyond the limit are simply not primed.
- **50 records per related list** — Only the first 50 records of any related list are primed.
- **Recommended maximum:** 100 parent Work Orders with 10 child records each

These limits are per-device sync session, not per technician record count.

### Conflict Resolution

When a technician syncs after working offline, two conflict resolution strategies are available:

| Strategy | Behavior | When to Use |
|---|---|---|
| `MERGE_ACCEPT_YOURS` | Local device changes win | Default. Use when technician's field data should override office changes during offline period |
| `MERGE_FAIL_IF_CONFLICT` | Sync fails on conflict — requires manual resolution | Use when data accuracy is critical and offline/server versions cannot be auto-merged |

`MERGE_ACCEPT_YOURS` is the default and most common. It means if a dispatcher updated a Work Order status in Salesforce while a technician was offline updating the same record, the technician's version wins after sync. This can cause unexpected overwrites.

### Server-Side Logic Is Deferred to Sync

**Critical architectural constraint:** Apex triggers, validation rules, and workflow rules do NOT fire when a technician updates records offline. They fire when the device syncs with the server.

Design implications:
- Validation rules that prevent incomplete data cannot catch offline errors until sync
- Apex triggers that send notifications or create related records don't fire in real-time during offline work
- FSL logic (scheduling engine re-evaluation, status transitions) fires at sync time, not at the moment of offline change

Build post-sync validation logic that reviews records updated during offline sessions.

### Ghost Records

A "ghost record" is a record that was deleted on the server while a technician's device was offline. When the device syncs, the deleted record still appears on the device until `cleanResyncGhosts()` is called via the FSL Mobile SDK.

Ghost records can cause technicians to:
- See appointments that were cancelled
- Navigate to Work Orders that no longer exist
- Attempt status transitions on deleted records (which silently fail)

Ghost record cleanup should be triggered automatically after each sync session via an SDK integration point.

---

## Common Patterns

### Priming Volume Design

**When to use:** Before any FSL Mobile deployment, to verify the implementation stays within priming limits.

**How it works:**
1. Calculate: average WOs per technician per day × average WOLIs per WO × average related objects per WOLI
2. Compare to the 1,000 page reference limit
3. If near the limit: reduce priming depth by excluding non-essential related objects
4. Test with a production-sized data load in sandbox before go-live

Example: 10 WOs × 8 WOLIs × 5 related records = 400 page references (safe). 10 WOs × 20 WOLIs × 6 related records = 1,200 page references (exceeds limit — silent failure).

### Conflict Resolution Strategy Selection

**When to use:** Any FSL Mobile deployment — decision must be made before go-live.

**Decision criteria:**
- If dispatcher office updates to active appointments are rare: MERGE_ACCEPT_YOURS (default)
- If dispatchers frequently update appointments technicians are actively working: MERGE_FAIL_IF_CONFLICT + build a conflict resolution UI
- If regulatory requirements mandate field data accuracy: MERGE_FAIL_IF_CONFLICT

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| High record volume per technician | Stay under 100 WOs / 10 children each | Keeps page references under 1,000 |
| Dispatcher + technician concurrent edits | MERGE_FAIL_IF_CONFLICT + resolution UI | Prevents silent data overwrites |
| Field-first operations (technician data primary) | MERGE_ACCEPT_YOURS (default) | Technician's offline work takes precedence |
| Ghost records persisting | Trigger cleanResyncGhosts() after each sync | Only mechanism to remove ghost records |
| Validation rules needed at job completion | Accept sync-time firing; build post-sync review | VRs don't fire offline — architectural reality |
| Custom object needs offline access | Add to priming hierarchy via Briefcase configuration | Only primed objects are available offline |

---

## Recommended Workflow

1. **Calculate priming volume** — Estimate page references for the average technician's daily schedule. Confirm within 1,000 page reference limit.
2. **Define conflict resolution strategy** — Choose MERGE_ACCEPT_YOURS or MERGE_FAIL_IF_CONFLICT. Document the decision and its implications for operations team.
3. **Design ghost record cleanup** — Integrate `cleanResyncGhosts()` into the post-sync SDK workflow.
4. **Map server-side logic to sync events** — List all Apex triggers and validation rules that touch FSL objects. Document that they fire at sync, not offline. Add post-sync review steps where needed.
5. **Configure Briefcase priming** — Configure which objects and record sets are primed. Test with production-representative data volume in sandbox.
6. **Test offline scenarios** — Simulate a 4-hour full-offline session with concurrent server edits. Verify sync behavior, conflict resolution, and ghost record handling.
7. **Train dispatchers on offline behavior** — Dispatchers must understand that changes to a technician's records during an offline session may be overwritten on sync (MERGE_ACCEPT_YOURS) or require manual resolution (MERGE_FAIL_IF_CONFLICT).

---

## Review Checklist

- [ ] Priming volume calculated and confirmed under 1,000 page reference limit
- [ ] Conflict resolution strategy decided and documented
- [ ] Ghost record cleanup (`cleanResyncGhosts()`) triggered post-sync
- [ ] Server-side automation (triggers, VRs) impact of sync-time firing understood
- [ ] Briefcase priming configured and tested with production-representative data
- [ ] Offline + sync tested with concurrent server-side edits
- [ ] Dispatcher team trained on offline sync behavior

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **1,000 page reference limit causes silent failure** — Records beyond the limit are simply not primed. There is no error. Technicians discover missing data at the job site.
2. **Ghost records persist until cleanResyncGhosts() is explicitly called** — Deleted server records stay on device. Technicians see cancelled appointments as active until cleanup is triggered.
3. **Apex triggers and validation rules fire at sync — not during offline work** — Data errors that would be caught by VRs in online mode pass silently during offline work and only surface at sync.
4. **MERGE_ACCEPT_YOURS (default) overwrites server changes with device changes** — This is correct most of the time but can silently overwrite dispatch-center updates made while the technician was offline.
5. **50 records per related list hard limit** — Only the first 50 related records are primed. Work orders with more than 50 line items will have incomplete data on the device.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Priming volume analysis | Page reference calculation for average technician schedule |
| Conflict resolution design decision | Strategy choice and operational impact documentation |
| Offline scenario test plan | Test cases for offline work, sync, conflict, and ghost record scenarios |

---

## Related Skills

- apex/fsl-custom-actions-mobile — Custom LWC actions that operate in the offline FSL Mobile context
- architect/fsl-integration-patterns — Integration patterns that need to account for sync-time trigger firing
