# Gotchas — Apex DML Patterns

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: DML limit counts operations, not rows

**What happens:** Developers who believe "150 DML" means "150 records" split their lists into batches of 150 and still hit the limit — or conversely, fear inserting large lists when they don't need to.

**When it occurs:** Any time a developer reasons about DML governor limits. One `Database.insert(5000Records)` uses 1 DML operation. One loop with 151 individual `insert` calls uses 151 DML operations and throws `LimitException`.

**How to avoid:** Always bulk records into a single list and call DML once outside any loop. Monitor `Limits.getDMLStatements()` in complex transactions with many conditional DML branches.

---

## Gotcha 2: Partial success rows are permanently committed

**What happens:** When using `Database.insert(list, false)`, rows that succeed are **immediately committed to the database**. There is no way to roll them back after the fact if a subsequent step fails.

**When it occurs:** Multi-step transactions where the first step uses `allOrNone=false` for partial tolerance, but a later step fails and the developer expects all rows to roll back together.

**How to avoid:** Use `Savepoint`/`Database.rollback()` when atomicity is required across multiple DML steps. Reserve `allOrNone=false` for truly independent row operations (e.g., bulk data loads where each row is independent).

---

## Gotcha 3: Database.merge is restricted to Account, Contact, and Lead

**What happens:** `Database.merge` throws a runtime `DmlException` when called on any object other than Account, Contact, or Lead. There is no compile-time error.

**When it occurs:** When a developer attempts to programmatically merge duplicate custom objects or other standard objects (e.g., Opportunity) using `Database.merge`.

**How to avoid:** Use `Database.merge` only for Account, Contact, or Lead. For other objects, implement custom deduplication logic (e.g., copy child records to the master, then delete the duplicate).

---

## Gotcha 4: DmlException vs. System.DmlException — catching matters

**What happens:** DML statements throw `System.DmlException` (accessible as `DmlException`), not `Exception`. If a catch block uses a parent type that doesn't include `DmlException`, the exception propagates uncaught.

**When it occurs:** Code that catches `Exception` generically will still catch `DmlException`. But code with a `catch (JSONException e)` before `catch (DmlException e)` — or that expects to catch only platform-specific exceptions — may miss DML failures.

**How to avoid:** When calling DML inside a try/catch, explicitly catch `DmlException` or `Exception`. For `Database` class partial-success mode (`allOrNone=false`), you do not need try/catch because failures appear in `SaveResult`, not exceptions.

---

## Gotcha 5: upsert with non-indexed external Id causes full table scan

**What happens:** `Database.upsert(list, ExternalId__c, false)` with a non-indexed external Id field causes a full table scan on each upsert, severely degrading performance on large objects.

**When it occurs:** When the custom field used as external Id is not marked as "External ID" (which auto-indexes it) in field setup, or when a formula field is mistakenly used.

**How to avoid:** Ensure the external Id field is marked as "External ID" in field metadata — this auto-creates an index. Verify with `Schema.DescribeFieldResult.isExternalId()` in Apex or check field setup in Setup > Object Manager.
