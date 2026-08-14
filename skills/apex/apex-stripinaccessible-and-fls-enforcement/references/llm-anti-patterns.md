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

**Correct pattern:** Use ONE primitive for the read path. `WITH USER_MODE` for new code; reserve `stripInaccessible(READABLE, ...)` for cases where the records came from somewhere other than a fresh query. The inverse error appears on classes saved at API 67.0+, where the query runs in user mode with no clause at all: that retires the *read* obligation, not the write one. `stripInaccessible(CREATABLE/UPDATABLE/UPSERTABLE, ...)` still belongs on DML assembled from user input, because user mode throws and fails the whole statement where the strip removes the field and continues — and an Apex trigger body runs in system mode at every API version, so the 67.0 default enforces nothing there.

**Detection hint:** Same method has `WITH USER_MODE` on a SOQL query AND a downstream `stripInaccessible(AccessType.READABLE, ...)` on its result. Flagged P2 by the checker. `WITH SECURITY_ENFORCED` does not count as the surviving primitive here — the checker flags the clause itself instead (P2 below apiVersion 67.0, P0 at 67.0+ where it no longer compiles).

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

---

## Anti-Pattern: Asserting That `stripInaccessible` Ignores Child/Subquery Records

**What the LLM generates:**

```apex
List<Account> accts = [SELECT Name, (SELECT LastName, Phone FROM Contacts) FROM Account];
SObjectAccessDecision d = Security.stripInaccessible(AccessType.READABLE, accts);

// "strip does not recurse into child collections" — so re-strip the children.
List<Contact> kids = new List<Contact>();
for (Account a : (List<Account>) d.getRecords()) { kids.addAll(a.Contacts); }
SObjectAccessDecision d2 = Security.stripInaccessible(AccessType.READABLE, kids);
// …and now reconcile two decision objects by hand
```

…and prose: "Parent strip does not recurse into child collections", "nested fields are NOT evaluated — strip child collections separately".

**Why it happens:** Two real facts get over-generalised. `SObjectAccessDecision` genuinely does return a *new* list rather than mutating the input, and the strip genuinely has no reach into records fetched by a separate query. From "it only touches what you pass it" the model infers "it only touches the top level of what you pass it", which does not follow. The direction of the error is fail-safe — it prescribes *more* stripping than necessary — and that is exactly why it survives review: nobody flags an over-cautious security claim, and the extra code passes its tests. It still costs real complexity, and it teaches an incorrect model of the API that leads to wrong conclusions elsewhere.

**Correct pattern:** Child records returned inside the collection you pass **are** evaluated. The Apex Developer Guide's own example applies `stripInaccessible(AccessType.READABLE, accountsWithContacts)` to `SELECT Name, (SELECT LastName, Phone FROM Contacts) FROM Account` and strips `Phone` from the child Contact rows. The method also "checks the source records for lookup or master-detail relationship fields to which the current user doesn't have access." One strip on the queried collection is sufficient for that collection. What genuinely is *not* covered: records from a separate query, and anything your code traverses after the fact. Strip each collection at its own query site. The supported nesting depth is not documented — do not assert a specific limit in either direction; verify with `System.runAs` if a design depends on it.

**Detection hint:** in prose, `(not|does ?n.t|NOT)\s+(recurse|evaluate|strip)[^.]{0,40}(child|nested|subquer)` — the claim is wrong as stated. In code, a second `Security.stripInaccessible` call whose input is built by flattening `getRecords()` from a first decision object is redundant work built on the misconception. Conversely, a genuine gap worth flagging is any SOQL result that reaches DML or a return value without passing through a strip or `WITH USER_MODE` at its own query site.
