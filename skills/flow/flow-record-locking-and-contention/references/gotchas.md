# Gotchas — Flow Record Locking And Contention

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

---

## Gotcha 1: Updating a Child Implicitly Locks the Parent

**What happens:** The corpus says "When you perform a DML operation on one record, related records are locked in addition to the record in question" (apexdev 264 L9409), and the Large Data Volumes guide lists "Minimizing parent record-locking conflicts" for changes to child records (ldv 264 L894-896). UNVERIFIED (2026-10-20): the Opportunity → Account example by name is Help-sourced. When a Flow updates an Opportunity, Salesforce takes a write lock on the parent Account row in addition to the Opportunity row. The Account lock is held for the entire duration of the Flow's transaction — not just the duration of the Update DML statement (locks last until the transaction completes, apexdev 264 L9383, L9392-9394).

**When it occurs:** Always, on every Update of any standard object that has a parent (Opportunity → Account, OpportunityLineItem → Opportunity → Account, Contact → Account, Case → Account, etc.). Custom objects with Master-Detail or Lookup relationships behave the same way (Master-Detail always; Lookup if the parent field is on the update payload or the lookup is reparented).

**How to avoid:** Recognize that any child-record flow contributes to parent contention. If the parent has high concurrent write traffic, decouple the parent update via Platform Event or Queueable so the user's transaction releases the parent lock immediately. There is **no flag** to disable the implicit parent lock (UNVERIFIED (2026-10-20): no corpus guide documents such a flag or its absence) — decoupling is the only mitigation.

---

## Gotcha 2: Queue-Owned Records Lock the Queue's Group Row

**What happens:** UNVERIFIED (2026-10-20): the Group-row lock is not in the corpus. When a record is owned by a queue (Cases, Leads, Tasks routed to a support queue), inserting or updating that record acquires a write lock on the queue's `Group` row. With many concurrent transactions inserting into the same queue, contention concentrates on that single Group row, not on the inserted records themselves.

**When it occurs:** High-volume case routing (web-to-case, email-to-case all routing to one inbound queue), bulk lead assignment to a queue, mass Task creation against a queue. The contention is invisible from the surface — the records being inserted are all different, but they share one parent (the Group).

**How to avoid:** Distribute load across multiple queues if possible (round-robin via assignment rules), or batch inserts so a single bulk DML acquires the Group lock once. For mass reassignment, schedule off-hours and process in chunks of <500.

---

## Gotcha 3: Master-Detail Reparenting Locks Both Parents

**What happens:** UNVERIFIED (2026-10-20): the lock behavior is Help-sourced and not in the corpus. Reassigning a Master-Detail child to a new master (via Update with the new master Id) takes write locks on **both** the old master and the new master simultaneously, in addition to the child row itself. With multi-level Master-Detail (e.g., LineItem → Opportunity → Account), reparenting at the bottom propagates locks all the way up, locking 4+ rows across two parent chains.

**When it occurs:** Master-Detail reparenting (allowed only when `reparentableMasterDetail = true` on the relationship; the default is false, api_meta 264 L45820-45822). Common in e-commerce schemas (line items moving between orders) and in Salesforce CPQ (Quote Lines moving between Quotes).

**How to avoid:** Reparenting is intrinsically lock-heavy. Schedule it off-hours, batch tightly, and accept that it cannot be fully decoupled — the new master lock is required for referential integrity. If reparenting is happening at high frequency, reconsider whether Master-Detail is the right relationship type (Lookup is much cheaper for reparenting).

---

## Gotcha 4: The 10-Second Lock Wait Is Invisible — And There Is No Retry Behind It

**What happens:** When DML cannot immediately acquire a row lock, the transaction **waits up to 10 seconds** for the lock to be released; "a DmlException is thrown" if the update's lock is not released within that time (apexdev 264 L9395-9398). The `UNABLE_TO_LOCK_ROW` code surfaces to the application (Flow fault path or Apex exception); UNVERIFIED (2026-10-20): the code and the Flow fault-path behavior are not in the corpus outside the parallel-test note (apexdev 264 L41979). Salesforce documents no automatic platform-level retry loop for this — no exponential backoff, no silent reattempt. One wait, then the fault.

The wait itself is what is invisible: the blocked transaction logs no element activity while it sits, so a debug log shows an unexplained multi-second gap that gets misattributed to whatever element happens to straddle it. UNVERIFIED (2026-10-20): the debug-log behavior is not in the corpus.

**When it occurs:** Any time a concurrent transaction holds the same row lock for more than 10 seconds — typically a parent Account or a queue Group row locked by a slow trigger, a callout, or a large loop upstream.

**How to avoid:** Treat any UNABLE_TO_LOCK_ROW fault as a serious signal — a full 10 seconds of contention is not a transient blip. But size the problem from fault *frequency* and from what held the lock, not from an imagined retry count: one fault email means one transaction gave up, not eleven attempts. Adding application-level retries does not help (it compounds contention and, in Flow, each Wait-based "retry" is a fresh transaction re-acquiring the lock from scratch; UNVERIFIED (2026-10-20): the Wait element's transaction behavior is not in the corpus). The fix is architectural decoupling. Monitor `EventLogFile` for `UNABLE_TO_LOCK_ROW` to detect contention building before it surfaces as a user-visible fault (UNVERIFIED (2026-10-20): the log type is not in the corpus).

---

## Gotcha 5: Flow's Automatic Rollback Masks the Partial State

**What happens:** When a Flow's DML element faults and there is no fault path connector (or the fault path doesn't issue a Salesforce-DML-rollback control), the Flow runtime **rolls back all DML the flow has performed in the current transaction** (UNVERIFIED (2026-10-20): not described in the corpus). From the user's perspective, the record they thought they updated is unchanged — no half-applied state, no audit trail showing the intent.

**When it occurs:** Any unhandled DML fault in a Flow. UNABLE_TO_LOCK_ROW is one common trigger; any limit breach (150 DML statements, 100 SOQL queries synchronously, apexdev 264 L19747, L19757) is another. The earlier text had the two numbers swapped.

**How to avoid:** Always wire a fault path on every DML element in production flows. Even if the fault path only logs to `Integration_Log__c`, the entry serves as evidence that the Flow ran and what it intended. Without the log, contention failures are silent data loss — the user thinks the change happened, the database disagrees, and there's no telemetry to debug from.

---

## Gotcha 6: Get Records Does Not Lock

**What happens:** Practitioners often assume that `Get Records` on an Account before `Update Records` on the same Account pre-locks the row, so a concurrent transaction cannot squeeze in a modification between the two steps. This is wrong. Get Records is a plain SOQL query and acquires no locks; the Apex Developer Guide locks only when you "embed the keywords FOR UPDATE after any inline SOQL statement" (apexdev 264 L9384). The Account row is only locked at the moment the Update Records DML fires. UNVERIFIED (2026-10-20): the corpus does not describe Get Records itself.

**When it occurs:** Any Flow that does Get → calculate → Update on the same record. Particularly dangerous for counter/sequence fields, where two concurrent flows could both Get the same value (say, 5), both compute new values (6 each), and both Update — losing one increment.

**How to avoid:** If you genuinely need read-modify-write atomicity, move the work to invocable Apex with `SELECT ... FOR UPDATE` (the lock is dropped by a later callout, apexdev 264 L9404-9408). For most flows, the right answer is to redesign so the operation is idempotent (e.g., set a field to a function of the trigger's $Record values, not to a value computed from a separate Get).

---

## Gotcha 7: Platform Event Subscribers Still Take Locks

**What happens:** Decoupling via Platform Event moves the parent update to a separate transaction (the subscriber). But the subscriber transaction still acquires the same parent lock when it issues the Update. The contention isn't eliminated; it's relocated to a different transaction (platform_events 264 L2187-2188). UNVERIFIED (2026-10-20): the "independent retry budget" of the earlier text; a flow subscriber has no documented retry, and only an Apex trigger retries, via `EventBus.RetryableException` (platform_events 264 L3258).

**When it occurs:** Always, when the subscriber updates a record. The benefit of the Platform Event pattern is not zero contention — it is **isolated** contention. The publisher's user-facing transaction completes immediately; the subscriber's contention is invisible to the user and batched: a flow can receive up to 200 event messages at once (platform_events 264 L2185). With the default Publish Immediately the subscriber can run before the publisher commits (platform_events 264 L346-348); set Publish After Commit when it must not.

**How to avoid:** Set realistic expectations. Platform Event decoupling solves the user-facing latency and avoids cascading contention across many concurrent user transactions. It does not magically eliminate the underlying contention on a hot parent row; if the subscriber consistently can't keep up, you may need to additionally batch (let events queue up and process every N seconds via the Pub/Sub API) or move the work to a Queueable Batchable.

---

## Gotcha 8: Account Skew Amplifies Lock Contention Non-Linearly

**What happens:** Account skew (>10,000 child records under one Account — Opportunities, Cases, Contacts; the LDV guide's deployment best practice is no parent with more than 10,000 children, ldv 264 L1052-1055) means the parent row is touched constantly. The Security Implementation Guide gives one documented case: "Salesforce locks the parent record of an activity when the activity history is updated ... avoid data skew" (secguide 262 L4707-4708). UNVERIFIED (2026-10-20): the read-hotspot and index-entry mechanism, and the "exponentially worse" Master-Detail claim below, are not in the corpus. Add lock contention from child-record updates and the Account row becomes a system-wide bottleneck.

**When it occurs:** Severe in B2C orgs with a "default Account" pattern (every Lead converts to a single Account because business contacts don't roll up to companies). Also common in support orgs with a "house account" for one-off cases.

**How to avoid:** Identify Account skew first (run the Skew Tester or query `SELECT AccountId, COUNT(Id) FROM Opportunity GROUP BY AccountId HAVING COUNT(Id) > 10000`). Resolve skew via account splitting or by switching the relationship to Lookup (Master-Detail with skew is exponentially worse). Lock-contention fixes layered on top of skew are palliative at best.

---

## Gotcha 9: Owner Change Locks Three Rows, Not One

**What happens:** UNVERIFIED (2026-10-20): the three-row lock below is not in the corpus; the Bulk API 2.0 guide lists "Updating ownership for records with private sharing" and "Updating user roles" as operations likely to cause lock contention (api_asynch 264 L2637-2639). Updating a record's `OwnerId` field acquires write locks on:

1. The record itself.
2. The old owner's `User` (or `Group`) row.
3. The new owner's `User` (or `Group`) row.

With mass reassignment (1,000 records moving from User A to User B), User A's row and User B's row are locked-and-released 1,000 times sequentially (or once if bulk DML). Either way, no other transaction can update either user during the window.

**When it occurs:** Mass reassignment via List View or screen flow. Also fires on Sales Cloud-style "round robin" assignment rules that distribute Leads across many users.

**How to avoid:** Bulk DML the reassignment (single Update of the full collection, not one Update per record). Schedule off-hours. For round-robin assignment, accept the per-user lock contention and ensure the assignment logic itself is fast (no heavy callouts holding the lock open).

---

## Gotcha 10: A Deferred Path May Run Under a Different User — Test the Permissions

**What happens:** UNVERIFIED (2026-10-20): the earlier text said a Scheduled Path runs the deferred work as the **Automated Process** user; the corpus does not say that for scheduled or asynchronous paths. What it does say for platform-event-triggered flows: "Debug logs ... appear under the Automated Process user. But each flow interview runs in the context of the user who published the event message" (platform_events 264 L2190-2192). Automated Process users "can't perform Object and FLS checks in custom code unless appropriate permission sets are explicitly applied to those users" (apexdev 264 L12106-12107). Treat the running user of a deferred path as something to verify, not assume.

**When it occurs:** Whenever you use a scheduled path or an asynchronous path as the decouple mechanism. Often surfaces as "the deferred work succeeded for some records but failed for others" — plausibly a sharing/permission asymmetry, not a contention issue (UNVERIFIED (2026-10-20): experience, not corpus).

**How to avoid:** Test the Scheduled Path branch with a low-permission test user and verify field-level access works. If the deferred work needs to know which user fired the trigger, capture `$User.Id` into a variable in the synchronous part of the flow and pass it through as a flow variable to the scheduled path.
