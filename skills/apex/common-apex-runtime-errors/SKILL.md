---
name: common-apex-runtime-errors
description: "Diagnosing and resolving common Apex runtime exceptions: NullPointerException, QueryException, DmlException, ListException, LimitException, TypeException. Use when debugging Apex runtime failures or writing defensive code. NOT for structuring try/catch — use apex/exception-handling. NOT for a cross-cutting error framework — use apex/error-handling-framework. NOT for governor-limit prevention — use apex/governor-limits."
category: apex
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Operational Excellence
triggers:
  - "Apex class throws NullPointerException and I don't know where the null is coming from"
  - "QueryException: List has more than 1 row for assignment to SObject — how do I fix this?"
  - "DmlException on insert failing with required field missing or duplicate value error"
  - "LimitException Too many SOQL queries in my trigger — what does that mean and how do I debug it?"
  - "Apex debug log shows FATAL_ERROR or EXCEPTION_THROWN event — how do I read it?"
  - "ListException Index was out of range — how do I trace the cause in Apex?"
  - "Fix MixedDmlException when inserting a User or PermissionSet alongside an Account in the same transaction"
  - "Resolve Unable to lock row / Record currently unavailable DmlException under bulk load"
tags:
  - NullPointerException
  - QueryException
  - DmlException
  - MixedDmlException
  - SObjectException
  - LimitException
  - TypeException
  - runtime-errors
  - debugging
  - exception-diagnosis
inputs:
  - Debug log with FATAL_ERROR or EXCEPTION_THROWN event, or a stack trace from a test failure
  - The Apex class or trigger name and approximate line number where the exception occurred
  - Exception class name (e.g. System.NullPointerException, System.QueryException)
outputs:
  - Per-exception root-cause diagnosis and corrective code pattern
  - Defensive coding checklist for the specific exception type encountered
  - Decision table mapping exception type to the correct resolution approach
dependencies: []
version: 1.1.0
author: Pranav Nagrecha
updated: 2026-07-07
---

# Common Apex Runtime Errors

Use this skill when an Apex class or trigger throws a runtime exception and you need to identify the root cause and apply the correct fix. It covers the six most common exception types — NullPointerException, QueryException, DmlException, ListException, LimitException, and TypeException/StringException — each with diagnosis path and resolution pattern.

---

## Before Starting

Gather this context before working on anything in this domain:

- Open the debug log for the failed transaction. Set log level to APEX_CODE: FINEST or at minimum APEX_CODE: ERROR. The `FATAL_ERROR` or `EXCEPTION_THROWN` event line contains the exception class, message, and line number.
- Confirm which Apex class and method (or trigger + handler) produced the failure. Automated test failures include a stack trace; production failures require a debug log or platform event capture.
- Know whether the execution is synchronous (trigger, Visualforce, REST callout) or asynchronous (Queueable, Batch, Scheduled). Async contexts suppress some exceptions from UI surfacing.

---

## Core Concepts

The Apex runtime throws built-in exceptions that are subclasses of `System.Exception`. Most are catchable in a `try/catch` block — but `LimitException` is explicitly uncatchable and must be prevented upstream. Each exception class carries a distinct message format that maps directly to a root cause.

### NullPointerException

Thrown when code dereferences a variable that is `null`. Common triggers:

- A SOQL query that returns no rows is assigned directly to an SObject variable (`Account a = [SELECT Id FROM Account WHERE Id = :someId];`). If zero rows match, `a` is `null`. Any field access on `a` (`a.Name`) throws immediately.
- An Apex method returns `null` and the caller chains a method call on the result without a null check.
- A `Map.get()` call returns `null` because the key is absent, and the return value is used without checking.

Resolution: Always check for `null` before accessing members. For SOQL scalars, wrap in a try/catch for `QueryException` or use a `List` and check `.isEmpty()`. For map lookups, use `map.containsKey(key)` before calling `.get()`.

### QueryException

Thrown in two scenarios:

1. **Too few rows:** A SOQL query assigned directly to a scalar SObject variable returns zero rows. Message: `List has no rows for assignment to SObject`.
2. **Too many rows:** The same scalar assignment returns two or more rows. Message: `List has more than 1 row for assignment to SObject`.

Resolution: Use a `List<SObject>` instead of a scalar when the result set size is uncertain. Check `list.isEmpty()` before accessing `list[0]`. When exactly one row is expected and a miss is a true error, catch `QueryException` explicitly and surface a meaningful error rather than letting the raw exception propagate.

### DmlException

Thrown when a DML operation (insert, update, delete, upsert) fails at the database level. Common causes:

- Required field is null on the record being inserted or updated.
- A duplicate rule fires and rejects the record.
- A before-trigger or validation rule blocks the record.
- **Row-lock contention** — `Unable to lock row - Record currently unavailable`. A transaction waits a maximum of 10 seconds for a lock to be released before timing out and throwing this error. It is one of the most frequently hit real-world DML failures, caused by concurrent DML on the same records, Apex triggers with long execution time, Bulk API loads in parallel mode, and Master-Detail child updates that all lock the same parent. See the dedicated Core Concept below.

Note: mixing an insert of two *non-setup* types (e.g. an `Account` and a `Contact`) into separate DML statements in one transaction is fine — that is not what triggers a mixed-DML failure. The mixed-DML restriction is specifically about setup vs non-setup objects; see **Mixed DML (`MIXED_DML_OPERATION`)** below.

The `DmlException` is the only common exception that carries per-row error details. Use `e.getNumDml()`, `e.getDmlMessage(i)`, `e.getDmlIndex(i)`, and `e.getDmlFields(i)` to extract which records failed and why.

Resolution: Validate required fields before DML. Use Database.insert/update/delete with `allOrNone=false` and inspect `Database.SaveResult[]` for partial-success scenarios. Log per-row `getDmlMessage` errors rather than only the top-level exception message.

### Mixed DML — `System.DmlException` with status code `MIXED_DML_OPERATION`

**There is no `MixedDmlException` type in Apex.** This is one of the most common wrong identifiers in the language. `catch (MixedDmlException e)` does not compile, and grepping production logs for `System.MixedDMLException` returns nothing. Mixed setup/non-setup DML raises an ordinary **`System.DmlException`** carrying the status code **`MIXED_DML_OPERATION`** — a real member of the API `StatusCode` enumeration. The log line looks like:

```text
System.DmlException: Insert failed. First exception on row 0; first error:
MIXED_DML_OPERATION, DML operation on setup object is not permitted after you
have updated a non-setup object (or vice versa): []
```

Catch it as a `DmlException` and discriminate on the message or on `e.getDmlType(0)`, not on a dedicated exception class.

It occurs when a DML operation on a *setup* object is mixed with a DML operation on a *non-setup* object in the same transaction. Per the official docs: "DML operations on certain sObjects, sometimes referred to as setup objects, can't be mixed with DML on non-setup sObjects in the same transaction." The restriction exists because some setup objects affect the running user's access to records.

- **Setup objects**, per the Apex Developer Guide list: `AuthSession`, `ContentWorkspace`, `FieldPermissions`, `ForecastingShare`, `Group`, `GroupMember`, `ObjectPermissions`, `ObjectTerritory2AssignmentRule`, `ObjectTerritory2AssignmentRuleItem`, `PermissionSet`, `PermissionSetAssignment`, `QueueSObject`, `RuleTerritory2Association`, `SetupEntityAccess`, `Territory`, `Territory2`, `Territory2Model`, `User`, `UserPackageLicense`, `UserRole`, `UserTerritory`, `UserTerritory2Association`.
- **Non-setup objects** are ordinary standard/custom records like `Account`, `Contact`, and custom objects.

The failure is *not* caused by mixing two arbitrary non-setup types. It fires only when a setup-object DML and a non-setup-object DML land in the same transaction.

Resolution: Run the setup-object DML in its own transaction. The standard fix is to move it into an asynchronous context — a `@future` method or a Queueable — so it executes in a separate transaction from the non-setup DML. In test code, `System.runAs()` blocks and async jobs called by the test are permitted to perform mixed DML.

### Row-lock contention — "Unable to lock row"

A distinct, very common `DmlException` variant: `Unable to lock row - Record currently unavailable`. Salesforce locks records during updates; a transaction can wait a maximum of 10 seconds for a lock to be released before timing out and throwing this error. Frequent sources are concurrent DML on the same records, long-running Apex triggers, Bulk API loads running in parallel mode, and Master-Detail child updates that contend for the same parent lock.

Resolution: Reduce trigger execution time and avoid explicit `FOR UPDATE` locking statements in triggers. For Bulk API loads, reduce batch size, switch from parallel to serial mode, or sort each batch by parent record ID so batches don't contend for the same parent locks. For Master-Detail, distribute child records across parents rather than concentrating them. Enable debug logs for the affected user to identify the offending trigger, flow, or validation rule.

### SObjectException

A built-in exception raised for problems with sObject records — most commonly attempting to change a field in an `update` statement that can only be set during `insert`, or accessing a field that was not included in the SOQL query. The docs describe it as covering "any problem with sObject records, such as attempting to change a field in an update statement that can only be changed during insert."

Resolution: Only write to fields that are updateable in the current DML context — never assign to read-only, formula, or insert-only fields on an existing record. Include every field you intend to read in the SOQL `SELECT` clause. This is one of many named built-in exceptions in Apex (the Apex Reference lists dozens, including `CalloutException`, `JSONException`, `SecurityException`, and `TypeException`); the six headline types in this skill are the most frequently hit, and `SObjectException` is a common near-neighbor worth recognizing on sight.

### ListException

Thrown when code accesses a List index that does not exist. Message: `List index out of bounds: N`. Common causes:

- `myList[0]` is accessed after the list was populated by a filtered SOQL query that returned no rows.
- A loop uses a manual index variable that increments past the list size.

Resolution: Check `list.size() > index` or `!list.isEmpty()` before indexed access. Prefer `for (SObject o : list)` iteration over manual index loops.

### LimitException — UNCATCHABLE

Thrown when a governor limit is exceeded: CPU time, SOQL queries, DML rows, heap size, callouts, and so on. Message examples: `Too many SOQL queries: 101`, `Apex CPU time limit exceeded`.

**LimitException cannot be caught with try/catch.** Any `catch (LimitException e)` block will never execute. The transaction is terminated by the platform immediately.

Resolution: Use `Limits.getQueries()` / `Limits.getLimitQueries()` guards before issuing SOQL inside loops. Bulkify triggers. Move heavy work to Queueable or Batch Apex. The `governor-limits` skill covers prevention patterns in depth.

### TypeException and StringException

`TypeException` is thrown when an explicit cast fails (e.g. casting an Integer to a Date) or when `JSON.deserialize` produces a type mismatch. `StringException` is thrown by `String.format()` when the argument count does not match the placeholder count.

Resolution: Validate input types before casting. Use `instanceof` for runtime type checks. Prefer `JSON.deserializeUntyped()` with manual type checks over strongly-typed deserialization when the input shape is uncertain.

---

## Common Patterns

### Pattern: SOQL-safe scalar assignment

**When to use:** Any time you expect exactly one row from a SOQL query but the data could theoretically return zero or multiple rows (i.e., almost always).

**How it works:**

```apex
List<Account> accounts = [SELECT Id, Name FROM Account WHERE Id = :recordId LIMIT 1];
if (accounts.isEmpty()) {
    throw new AuraHandledException('Account not found: ' + recordId);
}
Account acc = accounts[0];
```

**Why not the alternative:** Direct scalar assignment `Account acc = [SELECT Id FROM Account WHERE Id = :recordId]` throws `QueryException` on zero rows and on two or more rows. Both failure modes are common in real orgs where data is inconsistent.

### Pattern: DML with per-row error capture

**When to use:** Bulk DML operations where partial success is acceptable and each failed row must be logged.

**How it works:**

```apex
List<Database.SaveResult> results = Database.insert(records, false);
for (Integer i = 0; i < results.size(); i++) {
    if (!results[i].isSuccess()) {
        for (Database.Error err : results[i].getErrors()) {
            System.debug('Row ' + i + ' failed: ' + err.getMessage()
                + ' Fields: ' + err.getFields());
        }
    }
}
```

**Why not the alternative:** `insert records;` with `allOrNone=true` (the default) rolls back the entire batch on a single-row validation failure, which is rarely the right behavior for bulk operations.

### Pattern: LimitException prevention guard

**When to use:** Any trigger or service method that issues SOQL inside a loop or recursively.

**How it works:**

```apex
if (Limits.getQueries() + 1 >= Limits.getLimitQueries()) {
    // Log and abort gracefully — do NOT attempt the query
    System.debug(LoggingLevel.ERROR, 'SOQL limit near — aborting query batch');
    return;
}
List<Contact> contacts = [SELECT Id FROM Contact WHERE AccountId IN :accountIds];
```

**Why not the alternative:** You cannot catch `LimitException`. If the limit is crossed, the transaction terminates with no opportunity to log or recover.

---

## Decision Guidance

| Exception | Root Cause | Resolution |
|---|---|---|
| NullPointerException on SObject field | SOQL returned 0 rows into scalar variable | Use List + isEmpty() check |
| NullPointerException on method chain | Method returned null, caller chained without guard | Add null check before chaining |
| QueryException: List has no rows | Scalar SOQL on zero-row result | Use List or catch QueryException |
| QueryException: List has more than 1 row | Scalar SOQL matched multiple rows | Add WHERE filters or use LIMIT 1 |
| DmlException: required field missing | Field blank on record before DML | Validate fields before insert/update |
| DmlException: duplicate value | Duplicate rule or unique constraint hit | Check for existing record first or use upsert |
| DmlException: Unable to lock row | Row-lock contention (concurrent DML, long triggers, Bulk API parallel mode, MD child updates) | Shorten triggers; Bulk API serial mode + batch sort by parent ID; distribute MD children |
| DmlException: MIXED_DML_OPERATION | Setup-object DML (User, Group, PermissionSet…) mixed with non-setup DML in one transaction. Note: there is **no** `MixedDmlException` type — catch `DmlException` | Defer setup-object DML to @future / Queueable so it runs in its own transaction |
| SObjectException | Writing an insert-only/read-only field on update, or reading a field not in the SELECT | Only update updateable fields; add the field to the SOQL SELECT |
| ListException: index out of bounds | Indexed access on empty or short list | Check list.size() before access |
| LimitException: Too many SOQL queries | SOQL inside loop | Bulkify: move SOQL outside loop |
| LimitException: CPU time exceeded | Nested loops or heavy string ops on large sets | Move work to Batch Apex |
| TypeException | Invalid cast or JSON type mismatch | Use instanceof check before cast |
| StringException | String.format argument count mismatch | Match placeholder count to argument list |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner diagnosing an Apex runtime exception:

1. Open the debug log or test failure stack trace. Locate the `FATAL_ERROR` or `EXCEPTION_THROWN` event line. Note the exception class, message text, and line number.
2. Match the exception class to the six types in this skill (NullPointerException, QueryException, DmlException, ListException, LimitException, TypeException/StringException). If the class is not one of these, escalate to the `exception-handling` skill.
3. For NullPointerException: identify the null source — SOQL scalar result, method return value, or map lookup. Apply null guard or switch to List-based SOQL pattern.
4. For QueryException: switch scalar SOQL assignment to `List<SObject>` and add isEmpty() guard. For DmlException: add `Database.insert/update/delete` with `allOrNone=false` and log per-row errors using `getDmlMessage(i)`.
5. For LimitException: confirm via `Limits.*` API whether the limit is being approached. Bulkify the operation. If the fix requires architectural changes (e.g. moving to Batch Apex), flag for design review.
6. Apply defensive code pattern from the relevant section above. Add or update a unit test that exercises the failure path (zero-row SOQL, DML validation failure, boundary index access) to confirm the fix holds under real data conditions.
7. Run `python3 skills/apex/common-apex-runtime-errors/scripts/check_common_apex_runtime_errors.py --manifest-dir force-app/main/default/classes` to scan for unguarded patterns in the codebase.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] No scalar SOQL assignment without a null guard or QueryException catch
- [ ] No DML statement that swallows failures silently (all DML errors are logged or surfaced)
- [ ] No SOQL query inside a for loop (bulkification verified)
- [ ] LimitException is not wrapped in a try/catch (it is uncatchable — prevention is the only path)
- [ ] Unit tests cover the zero-row, multi-row, and validation-failure paths for all affected methods
- [ ] Debug log reviewed for EXCEPTION_THROWN events at ERROR or FATAL level before closing the issue

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **LimitException is uncatchable** — Unlike every other built-in exception, `System.LimitException` cannot be caught in a `try/catch` block. Code that wraps DML or SOQL in try/catch and expects to catch a limit breach will silently fail to catch it. The transaction terminates without entering any catch block.
2. **Null SOQL scalar vs. empty List** — `Account a = [SELECT Id FROM Account WHERE Id = :id]` returns `null` when zero rows match, but a `List<Account>` query returns an empty list. Many developers expect the scalar form to throw `QueryException` immediately, but the exception is deferred to the first field access on the null reference, making stack traces misleading.
3. **DmlException row index mismatch after partial-success** — When using `Database.insert(records, false)`, the `SaveResult` array index maps to the original `records` list, not a filtered list of failed records. Using `getDmlIndex(i)` on the exception (from `allOrNone=true` mode) is required to find the source record; iterating the result array directly gives you the right index only in `allOrNone=false` mode.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Corrective code diff | Replace unsafe SOQL scalar / unguarded DML / indexed list access with the safe pattern for the specific exception type |
| Defensive checklist | Per-exception review checklist confirming all failure paths are covered |
| Checker report | Output of `check_common_apex_runtime_errors.py` listing unguarded patterns in the scanned Apex class directory |

---

## Related Skills

- `exception-handling` — Use for structuring try/catch/finally blocks and custom exception class design; this skill covers per-exception diagnosis, not framework structure
- `governor-limits` — Use for systematic governor limit prevention strategies; this skill covers LimitException diagnosis only
- `error-handling-framework` — Use for org-wide error capture, logging, and alerting patterns
- `debug-logs-and-developer-console` — Use for navigating debug logs and setting log levels to capture EXCEPTION_THROWN events
