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

## Gotcha 5: Tests without `System.runAs` bypass FLS — strips become no-ops

**What happens:** A test that calls `Security.stripInaccessible` without `System.runAs(nonAdmin)` runs as the user executing the test, normally an admin with access to everything. The strip returns the input list unchanged. The test asserts "the records were processed" and passes — proving nothing about FLS enforcement.

**When it occurs:** Unit tests written by developers who forget that without `runAs` there is no restricted user for the strip to restrict. Below API 67.0 the class also ran in system mode by default; at 67.0+ database operations default to user mode, but the trap survives the change unaltered — `stripInaccessible` has always evaluated the *running user's* FLS, and that user is still an admin.

**How to avoid:** Always wrap FLS enforcement assertions in `System.runAs(testUser)` where `testUser` has a profile that explicitly lacks the field permissions you want to verify. Use the `templates/apex/tests/TestUserFactory` (per `templates/README.md`) to construct the restricted user.

---

## Gotcha 6: Your tests are the first user-mode caller — they fail at deploy time unless they run as a permissioned user

**What happens:** Gotcha 5 above is the mild version: no `runAs`, so the strip is a no-op and the test proves nothing. There is a harder version, and it does not fail quietly. When the custom fields ship in the *same deployment* as the enforcing code, a validate-only deploy (`sf project deploy start --dry-run --test-level RunSpecifiedTests`) compiles every component clean and then fails every test method before a single assertion runs:

```
System.QueryException: No such column 'Tier2_Notified_At__c' on entity 'Case'.
System.DmlException: Operation failed due to fields being inaccessible on Sobject Integration_Failure__c, check errors on Exception or Result!
```

Nothing in either message says "permissions", so the first instinct is to hunt for a field missing from `package.xml` that is, in fact, present and deployed `ok`.

**When it occurs:** The deploying user is a System Administrator, the permission set in the deployment carries the field permissions, and no test assigns it. Profile deployment overlays existing target-org settings, so a profile absent from the request keeps the FLS it already had — which, for a field this deployment just created, is none. The suite therefore reads and writes as a user with no FLS on its own new fields. `Security.stripInaccessible` is only half the exposure: `WITH USER_MODE` SOQL throws rather than strips, and from API 67.0 that is the default access mode for every new class, so the trap arrives without anyone opting into it.

**How to avoid:** Treat the `System.runAs` user as a deployment dependency rather than a test-quality flourish. Build it with `templates/apex/tests/TestUserFactory.cls`, assign the permission set(s) the deployment ships, and put the bodies inside `System.runAs(testUser)`. Do not count `System.runAs(new User(Id = UserInfo.getUserId()))` — that is the mixed-DML fence and re-enters the same user's context with the same (absent) permissions.

The full rule, the corpus citations, a worked class and the checker that enforces it live in `skills/apex/test-class-standards/`:

- rule and workflow placement — `skills/apex/test-class-standards/SKILL.md` § Recommended Workflow step 3
- the failure in detail — `skills/apex/test-class-standards/references/gotchas.md` Gotcha 13
- worked test class — `skills/apex/test-class-standards/references/examples.md` Example 5
- automated detection — `check_test_class_standards.py` rule `user-mode-test-without-runas` (ERROR), which fires when a non-test class in the tree carries `stripInaccessible`, `WITH USER_MODE`, `AccessLevel.USER_MODE` or `WITH SECURITY_ENFORCED` and the test class beside it has no permissioned `runAs`

**Evidence:** `.sfskills/builds/tier2-webhook/reports/mock-deploy/2026-09-12T13-08-43Z/summary.md` — 38 components `ok`, 28 of 28 test methods failed, coverage 34.9%.
