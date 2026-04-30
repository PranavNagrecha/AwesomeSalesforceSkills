---
name: field-level-security-in-async-contexts
description: "Use when async Apex (Queueable, Batch, Schedulable, @future) needs to honor the originating user's field-level security but the framework runs the job in a different security context than the user who initiated it. Triggers: 'fls bypassed in batch apex', 'queueable runs as wrong user', 'stripInaccessible in async returns full record', 'WITH USER_MODE evaluating against system user', 'scheduled apex sees fields the original user could not'. NOT for synchronous FLS enforcement (use apex-stripinaccessible-and-fls-enforcement) or for the with/without sharing decision (use apex-with-without-sharing-decision)."
category: apex
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Reliability
triggers:
  - "my batch apex updates fields the original user can't edit"
  - "WITH USER_MODE in queueable evaluates against the wrong user"
  - "stripInaccessible returns the full record in scheduled apex"
  - "@future method bypasses FLS that worked in the trigger"
  - "FLS enforcement disappears when work moves into Queueable.execute"
tags:
  - apex
  - security
  - field-level-security
  - async
  - queueable
  - batch
  - schedulable
inputs:
  - "the entry point that enqueues the async work (trigger, controller, REST, scheduler)"
  - "the user identity whose FLS the async job must respect (often not the system or scheduler user)"
  - "what the async job reads, writes, or surfaces (UI, callout payload, persisted record)"
outputs:
  - "patterns that capture and propagate the originating user's identity into the async job"
  - "FLS enforcement at the async-job boundary (USER_MODE / stripInaccessible scoped to that user)"
  - "tests that exercise the async job under multiple FLS profiles"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-30
---

# Field-Level Security in Async Contexts

Activate when Apex code that started in one user's transaction is continued asynchronously (Queueable, Batch, Schedulable, `@future`) and the FLS rules that applied in the original transaction must still apply in the async job. The skill produces a pattern for capturing and re-applying the originating user's FLS, plus tests that catch silent bypass.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Who enqueued the work, and who runs it?** A trigger fired by user A enqueues a Queueable. The Queueable's `execute()` runs as user A only because the trigger's transaction continues; but a Batch job *kicked off* by user A from `Database.executeBatch()` runs in *each batch slice* as user A as well — yet a Scheduled Apex job runs as the user who scheduled it, which may be a sysadmin who set up the schedule years ago. Get this straight before reasoning about FLS.
- **What FLS does the async job need to respect?** Sometimes the requirement is "honor the user who pressed the button" (most UIs); sometimes it's "honor a service identity" (integration jobs); sometimes it's "system context, do everything" (cleanup jobs). The wrong choice silently leaks or blocks fields.
- **Where does the data leave the system?** FLS enforcement matters most at the boundary: writing to a record (DML), returning to a UI, or sending to an external callout. An async job that *only* logs IDs internally has lower FLS surface than one that emails a CSV export.

---

## Core Concepts

### Async transitions change the user-mode evaluation point, not the user

The user that an async job runs as is determined at *enqueue* time, not at *execute* time. Specifically:

| Async surface | Running user |
|---|---|
| Queueable / `@future` | The user who enqueued the job — same as the original synchronous transaction |
| `Database.executeBatch()` | The user who called `executeBatch()`. If that was an Apex Scheduler firing, the user is whoever scheduled the scheduler |
| `System.schedule()` / scheduled Apex | The user who scheduled the job (often a long-departed sysadmin) — most common source of FLS surprises |
| Platform-Event-triggered Apex (`after insert` on `__e`) | The **Automated Process** user, which bypasses FLS and CRUD entirely — documented but routinely missed |

`WITH USER_MODE`, `WITH SECURITY_ENFORCED`, and `Security.stripInaccessible()` all evaluate against `UserInfo.getUserId()` *at the moment the call executes*. They don't know which user originally requested the work. If the requesting user and the running user differ, the security check answers a different question than the practitioner expected.

### `WITH USER_MODE` in async ≠ "the user who pressed the button"

A Queueable enqueued from a trigger that ran as user A *will* execute as user A. But a Batch job kicked off from a scheduled job that runs as a sysadmin *will* run as that sysadmin in every `execute()` call. `WITH USER_MODE` evaluates against the latter. The check passes because the sysadmin sees everything — and FLS-restricted fields slip into exports, callouts, and persisted records.

### Platform Event subscribers and the Automated Process user

Apex triggers on Platform Events run as the **Automated Process** user. This user is a system identity with full FLS access — `WITH USER_MODE` returns the full schema, `stripInaccessible` strips nothing. Treat PE-subscribed Apex as `system mode` regardless of whether you wrote `WITH USER_MODE`. To enforce FLS as the publisher-user, the publisher must put the user ID in the event payload (as a custom field) and the subscriber must use `System.runAs(...)` — but `runAs` only works in tests, so production code needs a different pattern (see Pattern 3).

---

## Common Patterns

### Pattern 1 — Carry the originating user ID through the async hop

**When to use:** Queueable or Batch chained from a user-initiated action where the async job runs as the same user — and you want to make that intent explicit and self-documenting in code (so a future maintainer doesn't refactor the entry point and silently change the running user).

**How it works:** Capture `UserInfo.getUserId()` at enqueue time, pass it to the Queueable constructor, and assert in `execute()` that the running user matches. The assertion is cheap and turns silent context drift into a loud test failure.

```apex
public class HighValueAccountSyncQueueable implements Queueable, Database.AllowsCallouts {
    private final Id originatingUserId;
    private final Set<Id> accountIds;

    public HighValueAccountSyncQueueable(Set<Id> accountIds) {
        this.accountIds = accountIds;
        this.originatingUserId = UserInfo.getUserId();
    }

    public void execute(QueueableContext qc) {
        if (UserInfo.getUserId() != originatingUserId) {
            throw new SecurityException(
                'Async context drifted: enqueued as ' + originatingUserId
                + ' but executing as ' + UserInfo.getUserId()
            );
        }
        // Now WITH USER_MODE meaningfully enforces FLS for the originating user.
        List<Account> rows = [
            SELECT Id, Name, AnnualRevenue
            FROM Account
            WHERE Id IN :accountIds
            WITH USER_MODE
        ];
        // ... continue
    }
}
```

**Why not the alternative:** Relying on "Queueable runs as the enqueuing user" without an explicit check looks correct today, but a future change — wrapping the enqueue in a Schedulable, retrying via `System.enqueueJob` from a PE handler — silently switches the running user. The assertion catches it.

### Pattern 2 — Re-apply FLS as a different user via stripInaccessible

**When to use:** Scheduled Apex or PE-triggered Apex that *must* respect a specific user's FLS even though the framework runs the code as a different identity (sysadmin scheduler, Automated Process user). Common in integration jobs that emit records to a downstream system on behalf of a service account whose visibility you want to honor.

**How it works:** Query the records first (the running user has access; this is fine for *reading*), then call `Security.stripInaccessible(AccessType.READABLE, records, ...)` with `accessLevel` parameters that simulate the target user. Since `stripInaccessible` has no public "evaluate as a different user" mode in production, the practical implementation is:

```apex
public static List<Account> applyTargetUserFls(
    List<Account> records,
    Id targetUserId
) {
    // No production API for "as user X" stripInaccessible, so we model it via a per-field FLS lookup.
    Map<String, Schema.DescribeFieldResult> describes =
        Account.SObjectType.getDescribe().fields.getMap();
    Map<Id, PermissionSetAssignment> psaByUser = ...; // pre-loaded for targetUserId

    Set<String> allowed = new Set<String>();
    for (Schema.SObjectField f : describes.values()) {
        Schema.DescribeFieldResult d = f.getDescribe();
        if (isFieldReadableForUser(d, targetUserId, psaByUser)) {
            allowed.add(d.getName());
        }
    }

    List<Account> stripped = new List<Account>();
    for (Account a : records) {
        Account copy = new Account(Id = a.Id);
        for (String fname : allowed) {
            copy.put(fname, a.get(fname));
        }
        stripped.add(copy);
    }
    return stripped;
}
```

The `isFieldReadableForUser` helper consults profile FLS and active permission sets for the target user. This is more code than `WITH USER_MODE`, but it's the only correct approach when the running user differs from the target user.

**Why not the alternative:** `WITH USER_MODE` evaluates against `UserInfo.getUserId()`. There is no "USER_MODE FOR :userId" syntax. Hand-rolling the FLS check is the only correct path for cross-user enforcement.

### Pattern 3 — Publish a synthesized "as-of" snapshot from the originating transaction

**When to use:** PE-triggered Apex where the subscriber runs as the Automated Process user and any synchronous "read with FLS" is meaningless. Instead of making the subscriber decide what's visible, the publisher decides at publish time and writes only FLS-clean data into the event.

**How it works:** In the publishing transaction (which runs as the originating user), call `Security.stripInaccessible(AccessType.READABLE, records)` and serialize the stripped result into the event payload. The subscriber is now safe regardless of its running user, because the unsafe fields never made it into the event in the first place.

```apex
// Publisher, in user context
List<Account> visibleToUser = Security.stripInaccessible(
    AccessType.READABLE,
    [SELECT Id, Name, AnnualRevenue, SSN__c FROM Account WHERE Id IN :ids]
).getRecords();

Account_Sync__e event = new Account_Sync__e(
    Originating_User_Id__c = UserInfo.getUserId(),
    Payload__c = JSON.serialize(visibleToUser)
);
EventBus.publish(event);
```

The subscriber deserializes and acts. No further FLS check is needed — the data was filtered before it entered the asynchronous channel.

**Why not the alternative:** Trying to enforce the publisher's FLS in the subscriber is impossible without re-implementing FLS lookup (Pattern 2). Filter at publish, not at subscribe.

---

## Decision Guidance

| Async context | Running user | FLS approach |
|---|---|---|
| Queueable enqueued from trigger / controller | Same as enqueuing user | `WITH USER_MODE` works; assert running user matches enqueueing user |
| `@future` method called from trigger | Same as calling user | Same as Queueable; pass userId for the assertion |
| Batch Apex from `Database.executeBatch()` in user context | Same as caller of executeBatch | `WITH USER_MODE`; document the calling-user contract on the Batch class |
| Scheduled Apex (`System.schedule`) | User who scheduled the job (often static sysadmin) | Re-apply target user FLS manually (Pattern 2) or run in system mode by design |
| PE-triggered Apex (`after insert` on `__e`) | Automated Process user (system) | Filter at publish (Pattern 3); subscriber is system-mode |
| Apex Scheduler firing a Batch | Scheduler user | Treat as scheduled Apex; not as the data owner |

---

## Recommended Workflow

1. Identify every async hop in the call chain — entry point → enqueue → execute. Note the running user at each step. Don't trust intuition; for Scheduled and PE paths, the running user is rarely the obvious one.
2. Decide which user's FLS the job must enforce: the originating user, a service identity, or the system. Document that contract on the async class.
3. If the contract is "originating user" and the framework guarantees it (Queueable, `@future`, in-transaction Batch), capture `UserInfo.getUserId()` at enqueue time and assert it in `execute()`.
4. If the contract is "originating user" but the framework runs as a different identity (Scheduled, PE), either re-apply FLS manually (Pattern 2) or filter at publish (Pattern 3). Pick filter-at-publish whenever feasible — it's simpler.
5. Add tests with multiple users: a sysadmin, a permission-restricted user, and a user with no FLS to a sensitive field. Run the async job for each and assert the output respects FLS. `Test.startTest`/`stopTest` runs Queueables synchronously; use `System.runAs` to stage the user context.
6. For Scheduled jobs, document in the class header which user the schedule was created under and what happens if that user is deactivated (Salesforce halts the job; this is sometimes desirable, sometimes a P0).
7. Review with security: any async path that emits to an external system must show its FLS-enforcement step explicitly. "Inherits user-mode from the trigger" is not a sufficient answer for Scheduled or PE paths.

---

## Review Checklist

- [ ] Every async class declares which user's FLS it honors (header comment or method contract)
- [ ] Queueable / @future / in-transaction Batch jobs assert running user matches the captured originating user
- [ ] Scheduled Apex either runs in declared system mode OR re-applies target user FLS manually
- [ ] PE-subscribed Apex is treated as system mode; publisher filters fields before publishing
- [ ] Tests cover the FLS-restricted case (a user without access to a sensitive field) and assert it isn't leaked
- [ ] No `WITH USER_MODE` claim is made about Scheduled or PE-triggered code without verifying the running user
- [ ] Static analysis flags `Security.stripInaccessible` calls inside Scheduled / PE handlers as suspicious

---

## Salesforce-Specific Gotchas

1. **Platform Event subscribers run as Automated Process** — Even when the publisher is a user, the `after insert` trigger on the `__e` object runs as the Automated Process user, which is a system identity that bypasses FLS and CRUD. `WITH USER_MODE` in the subscriber returns the full schema and `stripInaccessible` strips nothing. This is the single most common FLS-in-async bug.
2. **Scheduled Apex runs as the schedule creator forever** — A scheduled job created two years ago by an admin who has since left runs forever as that user (until deactivated). FLS in the job evaluates against that user's profile, not the org's current state. Deactivating the user halts the job — sometimes catching teams off guard.
3. **`Test.startTest()` / `Test.stopTest()` runs Queueables synchronously** — In tests, the Queueable's `execute()` runs as part of the test method's transaction, so the running user is the `runAs` user. This is convenient for testing but means tests pass even when the production async hop would change users. Always test under multiple `runAs` blocks to catch cross-user bugs.
4. **`@future(callout=true)` cannot accept sObjects** — Only primitive types and collections of primitives. So you cannot pass a `List<Account>` already filtered by `stripInaccessible` into a `@future` method. You must pass IDs and re-query inside, which re-evaluates FLS as the (correctly inherited) calling user. Awareness matters; the inherited user is fine, but the re-query is needed.
5. **`Database.Stateful` Batch jobs preserve member fields across `execute()` calls — but the running user is constant** — Once a Batch job is started, every `execute()` runs as the user who called `executeBatch()`. There is no per-slice user switch. Stateful fields preserve data, not security context.
6. **Apex Approval Process callbacks run as the user processing the approval** — Not the user who submitted. Custom callbacks that re-fetch the submitted record with `WITH USER_MODE` see the approver's FLS, not the submitter's. The original record's data is stripped of fields the approver can't see.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Originating-user-capture pattern | Apex class snippet that captures `UserInfo.getUserId()` at enqueue and asserts in execute |
| Cross-user FLS helper | Apex utility that strips records to a target user's FLS without using `WITH USER_MODE` |
| Filter-at-publish pattern | Publisher-side `stripInaccessible` snippet that pre-filters before serializing into a Platform Event payload |
| Multi-user test suite template | Test class structure with `System.runAs` blocks for sysadmin, restricted user, and PE/Automated Process simulation |

---

## Related Skills

- `apex/apex-stripinaccessible-and-fls-enforcement` — for the underlying FLS enforcement primitives in synchronous code; this skill builds on those by addressing the cross-context cases
- `apex/apex-with-without-sharing-decision` — for the orthogonal question of record-level sharing across the same async transitions
- `apex/long-running-process-orchestration` — for Queueable chaining patterns that pair with the originating-user-capture pattern here
- `architect/security-architecture-review` — for the broader review checklist that should include async FLS as a discrete check
