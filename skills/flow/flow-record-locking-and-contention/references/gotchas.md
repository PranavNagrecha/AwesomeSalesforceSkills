# Gotchas — Flow Record Locking And Contention

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

---

## Gotcha 1: Updating a Child Implicitly Locks the Parent

**What happens:** When a Flow updates an Opportunity, Salesforce takes a write lock on the parent Account row in addition to the Opportunity row. The Account lock is held for the entire duration of the Flow's transaction — not just the duration of the Update DML statement.

**When it occurs:** Always, on every Update of any standard object that has a parent (Opportunity → Account, OpportunityLineItem → Opportunity → Account, Contact → Account, Case → Account, etc.). Custom objects with Master-Detail or Lookup relationships behave the same way (Master-Detail always; Lookup if the parent field is on the update payload or the lookup is reparented).

**How to avoid:** Recognize that any child-record flow contributes to parent contention. If the parent has high concurrent write traffic, decouple the parent update via Platform Event or Queueable so the user's transaction releases the parent lock immediately. There is **no flag** to disable the implicit parent lock — decoupling is the only mitigation.

---

## Gotcha 2: Queue-Owned Records Lock the Queue's Group Row

**What happens:** When a record is owned by a queue (Cases, Leads, Tasks routed to a support queue), inserting or updating that record acquires a write lock on the queue's `Group` row. With many concurrent transactions inserting into the same queue, contention concentrates on that single Group row, not on the inserted records themselves.

**When it occurs:** High-volume case routing (web-to-case, email-to-case all routing to one inbound queue), bulk lead assignment to a queue, mass Task creation against a queue. The contention is invisible from the surface — the records being inserted are all different, but they share one parent (the Group).

**How to avoid:** Distribute load across multiple queues if possible (round-robin via assignment rules), or batch inserts so a single bulk DML acquires the Group lock once. For mass reassignment, schedule off-hours and process in chunks of <500.

---

## Gotcha 3: Master-Detail Always Locks Both Parents on Reparent

**What happens:** Reassigning a Master-Detail child to a new master (via Update with the new master Id) takes write locks on **both** the old master and the new master simultaneously, in addition to the child row itself. With multi-level Master-Detail (e.g., LineItem → Opportunity → Account), reparenting at the bottom propagates locks all the way up, locking 4+ rows across two parent chains.

**When it occurs:** Master-Detail reparenting (allowed only when `reparentableMasterDetail = true` on the relationship). Common in e-commerce schemas (line items moving between orders) and in Salesforce CPQ (Quote Lines moving between Quotes).

**How to avoid:** Reparenting is intrinsically lock-heavy. Schedule it off-hours, batch tightly, and accept that it cannot be fully decoupled — the new master lock is required for referential integrity. If reparenting is happening at high frequency, reconsider whether Master-Detail is the right relationship type (Lookup is much cheaper for reparenting).

---

## Gotcha 4: The 10-Retry Exponential Backoff Is Invisible

**What happens:** When DML fails to acquire a lock, Salesforce automatically retries up to **10 times** with exponential backoff before surfacing the failure to the application (Flow fault path or Apex exception). The retries happen transparently — there is no log entry, no event, no fault email until the 11th attempt fails.

**When it occurs:** Every UNABLE_TO_LOCK_ROW that surfaces in a fault path has been preceded by 10 silent retries. By the time you see one fault email, the system has been under contention for ~10–30 seconds. Across all concurrent transactions, hundreds or thousands of retries may have happened invisibly.

**How to avoid:** Treat any UNABLE_TO_LOCK_ROW fault as a serious signal — not a transient blip. The platform has already exhausted its retry budget. Adding application-level retries on top will not help (it just compounds the contention). The fix is architectural decoupling. Monitor `EventLogFile` for `UNABLE_TO_LOCK_ROW` to detect contention building up before it surfaces as a user-visible fault.

---

## Gotcha 5: Flow's Automatic Rollback Masks the Partial State

**What happens:** When a Flow's DML element faults and there is no fault path connector (or the fault path doesn't issue a Salesforce-DML-rollback control), the Flow runtime **rolls back all DML the flow has performed in the current transaction**. From the user's perspective, the record they thought they updated is unchanged — no half-applied state, no audit trail showing the intent.

**When it occurs:** Any unhandled DML fault in a Flow. UNABLE_TO_LOCK_ROW is one common trigger; any DML governor breach (100 DML statements, 150 SOQL queries, etc.) is another.

**How to avoid:** Always wire a fault path on every DML element in production flows. Even if the fault path only logs to `Integration_Log__c`, the entry serves as evidence that the Flow ran and what it intended. Without the log, contention failures are silent data loss — the user thinks the change happened, the database disagrees, and there's no telemetry to debug from.

---

## Gotcha 6: Get Records Does Not Lock

**What happens:** Practitioners often assume that `Get Records` on an Account before `Update Records` on the same Account pre-locks the row, so a concurrent transaction cannot squeeze in a modification between the two steps. This is wrong. Get Records is a plain SOQL query and acquires no locks. The Account row is only locked at the moment the Update Records DML fires.

**When it occurs:** Any Flow that does Get → calculate → Update on the same record. Particularly dangerous for counter/sequence fields, where two concurrent flows could both Get the same value (say, 5), both compute new values (6 each), and both Update — losing one increment.

**How to avoid:** If you genuinely need read-modify-write atomicity, move the work to invocable Apex with `SELECT ... FOR UPDATE`. For most flows, the right answer is to redesign so the operation is idempotent (e.g., set a field to a function of the trigger's $Record values, not to a value computed from a separate Get).

---

## Gotcha 7: Platform Event Subscribers Still Take Locks

**What happens:** Decoupling via Platform Event moves the parent update to a separate transaction (the subscriber). But the subscriber transaction still acquires the same parent lock when it issues the Update. The contention isn't eliminated; it's relocated to a different transaction and a different (independent) retry budget.

**When it occurs:** Always, when the subscriber updates a record. The benefit of the Platform Event pattern is not zero contention — it is **isolated** contention. The publisher's user-facing transaction completes immediately; the subscriber's contention is invisible to the user and self-throttling because events naturally batch.

**How to avoid:** Set realistic expectations. Platform Event decoupling solves the user-facing latency and avoids cascading contention across many concurrent user transactions. It does not magically eliminate the underlying contention on a hot parent row; if the subscriber consistently can't keep up, you may need to additionally batch (let events queue up and process every N seconds via the Pub/Sub API) or move the work to a Queueable Batchable.

---

## Gotcha 8: Account Skew Amplifies Lock Contention Non-Linearly

**What happens:** Account skew (>10,000 child records under one Account — Opportunities, Cases, Contacts) means the parent row is touched constantly. When skew is severe, the Account row is also a hotspot for read traffic (every child query on `WHERE AccountId = X` touches the index entry pointing at the Account). Add lock contention from child-record updates and the Account row becomes a system-wide bottleneck.

**When it occurs:** Severe in B2C orgs with a "default Account" pattern (every Lead converts to a single Account because business contacts don't roll up to companies). Also common in support orgs with a "house account" for one-off cases.

**How to avoid:** Identify Account skew first (run the Skew Tester or query `SELECT AccountId, COUNT(Id) FROM Opportunity GROUP BY AccountId HAVING COUNT(Id) > 10000`). Resolve skew via account splitting or by switching the relationship to Lookup (Master-Detail with skew is exponentially worse). Lock-contention fixes layered on top of skew are palliative at best.

---

## Gotcha 9: Owner Change Locks Three Rows, Not One

**What happens:** Updating a record's `OwnerId` field acquires write locks on:

1. The record itself.
2. The old owner's `User` (or `Group`) row.
3. The new owner's `User` (or `Group`) row.

With mass reassignment (1,000 records moving from User A to User B), User A's row and User B's row are locked-and-released 1,000 times sequentially (or once if bulk DML). Either way, no other transaction can update either user during the window.

**When it occurs:** Mass reassignment via List View or screen flow. Also fires on Sales Cloud-style "round robin" assignment rules that distribute Leads across many users.

**How to avoid:** Bulk DML the reassignment (single Update of the full collection, not one Update per record). Schedule off-hours. For round-robin assignment, accept the per-user lock contention and ensure the assignment logic itself is fast (no heavy callouts holding the lock open).

---

## Gotcha 10: Scheduled Path Runs As Automated Process User — Different Sharing

**What happens:** Decoupling via Scheduled Path on a record-triggered flow runs the deferred work as the **Automated Process** user, not as the user who fired the trigger. This avoids per-user contention but changes the security context — Automated Process bypasses many sharing rules but cannot perform some user-context operations (no User-specific Custom Permissions, no UserInfo.getUserId() pointing at a real user).

**When it occurs:** Whenever you use Scheduled Path or async record-triggered flow as the decouple mechanism. Often surfaces as "the deferred work succeeded for some records but failed for others" — actually a sharing/permission asymmetry, not a contention issue.

**How to avoid:** Test the Scheduled Path branch with a low-permission test user and verify field-level access works. If the deferred work needs to know which user fired the trigger, capture `$User.Id` into a variable in the synchronous part of the flow and pass it through as a flow variable to the scheduled path.
