# Gotchas — Apex stripInaccessible and FLS Enforcement

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Parent-child relationships are NOT recursively stripped

**What happens:** `Security.stripInaccessible(AccessType.UPDATABLE, cases)` evaluates fields directly on each Case but does NOT descend into populated lookup relationships like `case.Contact.*` or child collections like `case.CaseComments`. Those nested SObjects pass through untouched, including fields the user cannot read or edit.

**When it occurs:** Anywhere a parent record carries populated relationships from a SOQL `SELECT ... (SELECT ... FROM CaseComments)` style query and you pass the parent list to stripInaccessible expecting full-tree enforcement.

**How to avoid:** Strip child collections as a separate call. Extract them, run a second `stripInaccessible` with the right AccessType, and recombine if needed. The shared `templates/apex/SecurityUtils.cls` only strips the top-level collection — wrap it for relationships.

---

## Gotcha 2: `getRemovedFields()` returns a Map keyed by SObject, not by record

**What happens:** Practitioners expect `getRemovedFields()` to be record-by-record. It is actually `Map<String, Set<String>>` keyed by SObject API name (e.g., `"Case"`) with a value of every field stripped across the WHOLE batch for that SObject. You cannot tell from the map which specific record had `Internal_Notes__c` removed — only that some Case in the batch did.

**When it occurs:** Any time you log or surface `getRemovedFields()` and need per-record granularity. For per-record detail, use `getModifiedRecords()` which returns `Map<Id, SObject>` of records whose contents were modified by the strip.

**How to avoid:** Use `getModifiedRecords()` when you need to know WHICH records were stripped. Use `getRemovedFields()` when you need to know WHICH fields across the batch were stripped. Combine both for full audit detail.

---

## Gotcha 3: `SObjectAccessDecision` is immutable — you cannot mutate `getRecords()` and have changes reflect

**What happens:** Developers occasionally do `decision.getRecords().add(extraRecord)` or mutate a returned record assuming the decision will continue to "track" it. The decision is a snapshot — subsequent edits to the returned list are just edits to a List<SObject>. Re-stripping is required if you mutate after the strip.

**When it occurs:** Multi-stage processing where post-strip code adds or modifies records and assumes a single strip call covers the whole pipeline.

**How to avoid:** Treat each strip call as a one-time gate. If records are added or modified after the strip, run another strip pass before DML.

---

## Gotcha 4: `AccessType.UPSERTABLE` is the INTERSECTION of CREATABLE and UPDATABLE, not the union

**What happens:** A field that is creatable but not updatable (or vice versa) gets stripped on `AccessType.UPSERTABLE`. Practitioners often expect UPSERTABLE to mean "creatable OR updatable" (whichever applies based on whether the row exists), but the platform applies BOTH constraints because at decision time it does not know which records will insert vs update.

**When it occurs:** Upsert flows where some fields are intentionally restricted to "set on create only" (e.g., `Source_System__c`). Those fields silently disappear on every upserted record.

**How to avoid:** If create-only or update-only fields matter, split the operation into separate insert and update lists with the matching CREATABLE / UPDATABLE strip per branch. Do not use upsert.

---

## Gotcha 5: Tests under default system context bypass FLS — strips become no-ops

**What happens:** A test that calls `Security.stripInaccessible` without `System.runAs(nonAdmin)` runs under the system test user, which has access to everything. The strip returns the input list unchanged. The test asserts "the records were processed" and passes — proving nothing about FLS enforcement.

**When it occurs:** Unit tests written by developers who forget that test code runs in system mode by default for FLS purposes.

**How to avoid:** Always wrap FLS enforcement assertions in `System.runAs(testUser)` where `testUser` has a profile that explicitly lacks the field permissions you want to verify. Use the `templates/apex/tests/TestUserFactory` (per `templates/README.md`) to construct the restricted user.
