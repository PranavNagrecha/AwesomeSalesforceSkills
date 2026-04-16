# Gotchas — Code Review Checklist Salesforce

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Partial success DML masks failures

**What happens:** `Database.insert(rows, false)` returns success for some rows while others fail; downstream code assumes all inserts succeeded and dereferences null ids or skips error handling.

**When it occurs:** Bulk data loads, integration handlers, or “resilient” triggers that swallow `Database.Error` entries.

**How to avoid:** Always iterate `SaveResult` / `UpsertResult`; for business-critical paths prefer all-or-nothing DML unless partial success is an explicit product requirement.

---

## Gotcha 2: Test visibility vs production sharing

**What happens:** Tests pass because `@TestSetup` or `runAs` creates data visible only in test context, while production code paths rely on sharing that is different under the real user.

**When it occurs:** Service classes tested only as admin; LWC controllers never tested as low-privilege profiles.

**How to avoid:** Add at least one `System.runAs` path for a constrained user when reviewing user-facing Apex; align test data with production profile constraints.

---

## Gotcha 3: Async fan-out and limit coupling

**What happens:** A queueable enqueues another queueable per record, or a batch `finish` schedules unbounded jobs, eventually tripping async limits or creating backlog storms.

**When it occurs:** Retry logic, “self-chaining” sync patterns moved to async without redesign.

**How to avoid:** Batch work into chunks; cap chaining depth; document expected job volume per upstream event in the review.
