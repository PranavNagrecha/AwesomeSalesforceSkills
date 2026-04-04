# Gotchas — Composite API Patterns

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: allOrNone=true Rolls Back Successfully Completed Subrequests

**What happens:** When `allOrNone: true` is set on a `/composite/` request and any single subrequest fails, Salesforce rolls back every subrequest in the call — including those that had already succeeded. The rolled-back subrequests report `"httpStatusCode": 400` and `"errorCode": "PROCESSING_HALTED"` in their individual composite response entries. This can be misread as failures of those subrequests rather than as rollback confirmation.

**When it occurs:** Any time a composite request uses `allOrNone: true` and a subrequest encounters a validation error, required field failure, or trigger exception. The outer HTTP response is still 200, which makes the rollback invisible unless the caller inspects every `compositeResponse` entry.

**How to avoid:** Always iterate `compositeResponse[]` and inspect `httpStatusCode` on every entry, even when `allOrNone: true`. Distinguish between `PROCESSING_HALTED` (rolled back due to another subrequest's failure) and genuine per-subrequest failures. Document in the integration design that `allOrNone: true` means "all succeed or none persist" — partial data is never possible.

---

## Gotcha 2: allOrNone=false Requires Explicit Per-Subrequest Error Handling

**What happens:** When `allOrNone: false` is used, each subrequest executes independently. A failure in subrequest 5 does not stop subrequests 6–25 from executing. The outer response is HTTP 200. If the caller only checks the outer status and returns success, it silently discards the errors from failed subrequests. Records that should have been created or updated are missing, and there is no exception raised or log entry unless the caller explicitly inspects each response.

**When it occurs:** Any composite or batch call with `allOrNone: false` where the caller does not iterate the full `compositeResponse[]` array. Common in integrations migrated from single-call patterns where a non-200 status was the only failure signal.

**How to avoid:** After every Composite API call with `allOrNone: false`, iterate the entire `compositeResponse[]` (or per-record results array for sObject Collection). Collect all entries where `httpStatusCode >= 400`. Route failed subrequests to a retry queue or dead-letter queue. Alert on persistent failures. Never treat the outer HTTP 200 as confirmation that all subrequests succeeded.

---

## Gotcha 3: referenceId Field Names Are Case-Sensitive

**What happens:** A subrequest sets `"referenceId": "NewAccount"`. A subsequent subrequest references `"@{newaccount.id}"` (different casing). Salesforce does not resolve the reference — it passes the literal string `"@{newaccount.id}"` as the field value. The dependent subrequest then fails with a field type mismatch or ID format error, and the error message does not mention that the referenceId was unresolved. The root cause is non-obvious.

**When it occurs:** Whenever a developer manually assembles the composite request body and inconsistently capitalizes the referenceId. Also common when referenceIds are generated programmatically from different string transformations (e.g., `ToUpper()` on declaration and `ToLower()` on reference).

**How to avoid:** Define all referenceId values as constants in the integration codebase. Use the same constant in both the declaration (`"referenceId": ACCOUNT_REF_ID`) and the reference (`"@{" + ACCOUNT_REF_ID + ".id}"`). The checker script in this skill's `scripts/` directory flags potential case inconsistency in composite request files.

---

## Gotcha 4: DML Governor Limits Are Not Waived Per Subrequest

**What happens:** Each subrequest's DML operations count against the same governor limit bucket as a standard Apex transaction. A composite request with 25 subrequests, each inserting 200 records via sObject Collection, generates 5,000 DML row operations. Apex triggers, workflow rules, and validation rules fired by those inserts consume additional CPU time and SOQL queries within the same transaction. Orgs with complex automation can hit the 150 DML statement limit or CPU time limit (10,000ms synchronous) within a single composite call.

**When it occurs:** High-volume composite requests against objects with complex trigger logic, Process Builder, or Flow automation. Also occurs when the integration team designs for the API limits (25 × 200) without accounting for Apex-side governor consumption.

**How to avoid:** Calculate DML row count before load testing: `subrequest_count × records_per_subrequest`. Profile trigger execution time per record on a sandbox. If governor pressure is detected, reduce subrequest count, split into multiple Composite calls, or switch to Bulk API 2.0 which runs in async context with higher DML limits.

---

## Gotcha 5: sObject Tree Has No Partial Success Mode

**What happens:** Unlike `/composite/` with `allOrNone: false`, the sObject Tree resource (`/composite/tree/`) always behaves as all-or-nothing. One invalid record anywhere in a 200-record tree payload causes the entire tree to roll back. There is no way to insert 199 valid records and skip the one invalid record.

**When it occurs:** Any `/composite/tree/` call where input data quality is not validated before submission. Common during initial data migration when source data has gaps (missing required fields, invalid picklist values, relationship IDs that do not exist in the target org).

**How to avoid:** Validate all records client-side before submitting a tree payload: check required fields, field length constraints, picklist values, and parent record IDs. For untrusted data sources, consider splitting into smaller trees or switching to `/composite/sobjects/` with `allOrNone: false` to allow partial success with error reporting per record.
