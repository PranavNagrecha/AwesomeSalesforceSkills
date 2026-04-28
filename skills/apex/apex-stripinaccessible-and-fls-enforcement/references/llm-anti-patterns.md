# LLM Anti-Patterns — Apex stripInaccessible and FLS Enforcement

Common mistakes AI coding assistants make when generating or advising on `Security.stripInaccessible`.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: DML on the original list after a strip call

**What the LLM generates:**

```apex
SObjectAccessDecision decision =
    Security.stripInaccessible(AccessType.CREATABLE, userSupplied);
insert userSupplied;   // wrong — strip is now a no-op
```

**Why it happens:** The model treats `stripInaccessible` as if it mutated the input list in place (Java/Python intuition). Apex returns a NEW list inside the decision object; the argument is untouched.

**Correct pattern:**

```apex
SObjectAccessDecision decision =
    Security.stripInaccessible(AccessType.CREATABLE, userSupplied);
insert decision.getRecords();
```

**Detection hint:** Same method contains both `Security.stripInaccessible(...)` and a DML on the original parameter name rather than the decision's `getRecords()`. Flagged P0 by `check_apex_stripinaccessible_and_fls_enforcement.py`.

---

## Anti-Pattern 2: Assuming child relationships are stripped recursively

**What the LLM generates:**

```apex
SObjectAccessDecision d = Security.stripInaccessible(AccessType.UPDATABLE, cases);
update d.getRecords();   // assumes case.Contact fields are also enforced
```

**Why it happens:** Models extrapolate from generic "deep enforcement" framing in security guides. Salesforce's strip is shallow — it evaluates fields directly on the SObjects in the collection passed in.

**Correct pattern:**

```apex
SObjectAccessDecision parents = Security.stripInaccessible(AccessType.UPDATABLE, cases);
List<Contact> nested = new List<Contact>();
for (Case c : (List<Case>) parents.getRecords()) {
    if (c.Contact != null) nested.add(c.Contact);
}
SObjectAccessDecision children =
    Security.stripInaccessible(AccessType.UPDATABLE, nested);
// ... DML each level appropriately
```

**Detection hint:** A parent collection is stripped, then child collections from the same payload are DML'd without their own strip pass.

---

## Anti-Pattern 3: Calling stripInaccessible from `@future` or batch with no user context

**What the LLM generates:**

```apex
@future
public static void asyncProcess(List<Account> recs) {
    Security.stripInaccessible(AccessType.UPDATABLE, recs); // running user is the original invoker, not "current user" intuition
    update recs;
}
```

**Why it happens:** The model treats async contexts as "system context" and either skips enforcement or mis-trusts the strip. In reality `@future` runs as the user who enqueued the job, so the strip DOES enforce — but only if the developer remembers and uses the result.

**Correct pattern:**

```apex
@future
public static void asyncProcess(List<Account> recs) {
    SObjectAccessDecision d = Security.stripInaccessible(AccessType.UPDATABLE, recs);
    update d.getRecords();
}
```

**Detection hint:** `@future` / `Queueable.execute` / `Database.Batchable.execute` method that calls strip but ignores the return value, OR comments claiming "system mode" inside an async method.

---

## Anti-Pattern 4: Double-enforcement (USER_MODE in SOQL + stripInaccessible after)

**What the LLM generates:**

```apex
List<Account> recs = [SELECT Id, Name FROM Account WITH USER_MODE];
SObjectAccessDecision d = Security.stripInaccessible(AccessType.READABLE, recs); // redundant
return d.getRecords();
```

**Why it happens:** Models pile on enforcement primitives "to be safe." `WITH USER_MODE` already throws on inaccessible read — the strip cannot strip anything that survived the query.

**Correct pattern:** Use ONE primitive for the read path. `WITH USER_MODE` for new code; reserve `stripInaccessible(READABLE, ...)` for cases where the records came from somewhere other than a fresh query.

**Detection hint:** Same method has `WITH USER_MODE` (or `WITH SECURITY_ENFORCED`) on a SOQL query AND a downstream `stripInaccessible(AccessType.READABLE, ...)` on its result. Flagged P2 by the checker.

---

## Anti-Pattern 5: Using `AccessType.READABLE` before a write

**What the LLM generates:**

```apex
SObjectAccessDecision d =
    Security.stripInaccessible(AccessType.READABLE, userSupplied);
insert d.getRecords();   // wrong AccessType for an insert
```

**Why it happens:** READABLE feels like the "safe default" and the model doesn't reason about which DML is about to occur. READABLE only checks read access — fields a user can read but cannot create will pass through and be persisted on insert.

**Correct pattern:** AccessType must match the operation: CREATABLE for `insert`, UPDATABLE for `update`, UPSERTABLE for `upsert`, READABLE only for outbound payloads (reads).

**Detection hint:** `Security.stripInaccessible(AccessType.READABLE, ...)` in the same method as `insert`, `update`, or `upsert`.
