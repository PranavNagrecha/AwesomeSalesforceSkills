# Gotchas — Code Review Checklist Salesforce

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Partial success DML masks failures

**What happens:** `Database.insert(rows, false)` returns success for some rows while others fail; downstream code assumes all inserts succeeded and dereferences null ids or skips error handling.

**When it occurs:** Bulk data loads, integration handlers, or “resilient” triggers that swallow `Database.Error` entries.

**How to avoid:** Always iterate `SaveResult` / `UpsertResult`; for business-critical paths prefer all-or-nothing DML unless partial success is an explicit product requirement. The Apex Developer Guide is explicit that with `allOrNone` set to false you must iterate the returned results to find which records failed.

---

## Gotcha 2: Test visibility vs production sharing

**What happens:** Tests pass because `@TestSetup` or `runAs` creates data visible only in test context, while production code paths rely on sharing that is different under the real user.

**When it occurs:** Service classes tested only as admin; LWC controllers never tested as low-privilege profiles.

**How to avoid:** Add at least one `System.runAs` path for a constrained user when reviewing user-facing Apex; align test data with production profile constraints.

---

## Gotcha 3: Async fan-out and limit coupling

**What happens:** A queueable enqueues another queueable per record, or a batch `finish` schedules unbounded jobs, eventually tripping async limits or creating backlog storms.

**When it occurs:** Retry logic, “self-chaining” sync patterns moved to async without redesign.

**How to avoid:** Batch work into chunks; cap chaining depth (the default chained-queueable stack depth in Developer and Trial Edition orgs is five, and `System.enqueueJob(queueable, asyncOptions)` lets you set a maximum depth); remember `System.enqueueJob` is capped at 50 calls per synchronous transaction and 1 per asynchronous one. Document expected job volume per upstream event in the review.

---

## Gotcha 4: An `apiVersion` bump silently changes access and sharing

**What happens:** A PR "only" raises a class from 66.0 to 67.0 to use a new language feature. After deploy, users get `QueryException` on fields they cannot read, and records that the class used to return disappear.

**When it occurs:** At API version 67.0 and later Apex runs database operations in user mode by default and classes without an explicit sharing declaration run `with sharing`; at 66.0 and earlier system mode is the default.

**How to avoid:** Treat every `apiVersion` change in a `-meta.xml` file as a behaviour change. Put an explicit sharing keyword on every class with database operations (the Apex Developer Guide recommends this) and re-run the permission-sensitive tests as the production persona before approving.

---

## Gotcha 5: Trigger sharing context depends on the trigger's version

**What happens:** A reviewer assumes "triggers run in system context" and approves a trigger that reads related records the running user cannot see; on a 67.0 trigger the unqualified query now returns fewer rows and downstream logic misfires. The opposite mistake also happens: a reviewer assumes FLS is enforced in a 66.0 trigger body.

**When it occurs:** Triggers cannot carry a sharing declaration and run without sharing, but on 67.0+ their SOQL, SOSL, and DML run in user mode unless `WITH SYSTEM_MODE` / `as system` is written, which re-applies the user's sharing.

**How to avoid:** Read the trigger's own `apiVersion`, then require an explicit access mode on every query or DML statement in the trigger and its handler so the intent survives the next version bump.

---

## Gotcha 6: 200 is the chunk size, not a ceiling on the request

**What happens:** A reviewer reasons "Bulk API sends 10,000 rows, so the trigger hits limits" or "UI saves one row, so the loop is fine". Both are wrong.

**When it occurs:** A large API request fires the trigger repeatedly on chunks of 200 records, and governor limits reset between those invocations for the same HTTP request. The Apex Developer Guide's trigger best-practices page shows that code written for one record does not support bulk operations invoked through SOAP API.

**How to avoid:** Review against one 200-record invocation: the code must stay inside the per-transaction limits for 200 rows, and a 200-row bulk test is the evidence.

---

## Gotcha 7: Active jobs block the deploy of a reviewed class

**What happens:** The PR is approved, the release starts, and the deploy fails because a scheduled or batch job references the changed Apex class.

**When it occurs:** By default you can't deploy updates to an Apex class while it has one or more active jobs; the Metadata API guide lists cancelling the jobs or enabling deployments with Apex jobs on the Deployment Settings page as the ways round it.

**How to avoid:** Ask in review whether any `Schedulable` or batch class is touched; add the job pause/reschedule step, or the confirmed Deployment Settings option, to the release plan before approval.
