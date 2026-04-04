# Dynamic Apex — Work Template

Use this template when building or reviewing Apex code that uses dynamic SOQL, dynamic SOSL, Schema describe methods, or dynamic field access via `record.get()` / `record.put()`.

---

## Scope

**Skill:** `dynamic-apex`

**Request summary:** (fill in what the user asked for — e.g., "build a generic multi-object export utility" or "review this dynamic query builder for injection risks")

---

## Context Gathered

Answer these before writing or reviewing any code:

- **Source of object/field names:**
  - [ ] Code-defined constants (lowest risk — no external validation needed beyond schema confirmation)
  - [ ] Admin-configured (custom metadata, Field Sets, custom settings) — must validate against Schema describe
  - [ ] User-supplied input — must use bind variables + Schema allowlist
- **Execution context:**
  - [ ] User-facing (AuraEnabled, REST, invocable) — FLS enforcement is required
  - [ ] System context (Batch, Scheduled, admin utility) — FLS enforcement may be intentionally relaxed; document explicitly
- **Loop/bulk behavior:**
  - [ ] Is this code called per-record or with lists? If bulk, describe caching is mandatory.
- **Existing tests:**
  - [ ] Does a `System.runAs()` test exist to verify FLS enforcement paths?

---

## Pattern Selection

Which pattern from SKILL.md applies to this task?

- [ ] **FLS-Enforced Dynamic Update Utility** — configurable field list + user-facing DML
- [ ] **Admin-Configurable Dynamic Query Builder** — Field Set or custom metadata field list + search/filter
- [ ] **Multi-Object Polymorphic Processor** — list of mixed sObject types, type-based routing
- [ ] **Other** — describe the pattern:

---

## Implementation Checklist

Copy this and tick items as you complete them.

**Injection and Input Validation**
- [ ] User-supplied filter values use bind variables (`:variableName`) in the query string.
- [ ] If bind variables are not available (SOSL FIND clause), `String.escapeSingleQuotes()` is applied.
- [ ] Object names are validated via `Schema.getGlobalDescribe().containsKey(name)` before use.
- [ ] Field names are validated via `DescribeSObjectResult.fields.getMap().containsKey(name)` before use.

**FLS Enforcement**
- [ ] `DescribeFieldResult.isAccessible()` checked before `record.get()` or inclusion in SELECT.
- [ ] `DescribeFieldResult.isUpdateable()` checked before `record.put()` or inclusion in DML.
- [ ] Object-level `isUpdateable()` / `isAccessible()` checked before DML or query.

**Performance**
- [ ] `Schema.getGlobalDescribe()` stored in a `static final` class-level variable.
- [ ] Per-object field maps cached in a `static` map, lazily populated, not re-fetched per record.
- [ ] No describe call inside a `for` / `while` loop body.

**Correctness**
- [ ] `record.get()` return values are explicitly cast with type verified via `DescribeFieldResult.getType()`.
- [ ] Field Set members are validated against the live field map before query construction.
- [ ] `WITH SECURITY_ENFORCED` usage is documented as intentional fail-fast, not graceful degradation.

**Testing**
- [ ] Test covers the happy path with accessible fields.
- [ ] Test covers the FLS-denied path using `System.runAs()` with a restricted profile or permission set.
- [ ] Test covers a non-existent field name to verify validation throws a clear error.
- [ ] Test covers bulk input (200 records) to confirm no `LimitException` from describe calls.

---

## Notes

Record any deviations from standard patterns and why. For example: "This utility runs in a Batch context; FLS enforcement is intentionally skipped because the job is admin-only. Documented in the class-level Javadoc."
