# LLM Anti-Patterns — Apex Savepoint and Rollback

Common mistakes AI coding assistants make with Database.Savepoint.

## Anti-Pattern 1: Rolling back after an HTTP callout

**What the LLM generates:**

```
Savepoint sp = Database.setSavepoint();
insert a;
Http h = new Http(); h.send(req);
if (bad) Database.rollback(sp);  // CalloutException
```

**Why it happens:** Model treats callouts as regular ops.

**Correct pattern:**

```
After any HTTP callout, rollback is forbidden. Restructure: make the
callout FIRST, inspect the response, then decide whether to commit
DML. If DML must precede the callout, accept that rollback is
unavailable — use compensating actions on failure.
```

**Detection hint:** Apex code with `new Http().send(...)` between `setSavepoint` and `rollback`.

---

## Anti-Pattern 2: Savepoint inside a loop

**What the LLM generates:**

```
for (Account a : accs) {
    Savepoint sp = Database.setSavepoint();
    insert a;
    ...
}
```

**Why it happens:** Model scopes savepoints too tightly.

**Correct pattern:**

```
setSavepoint counts as a DML statement. Looping hits the 150 DML
statement limit quickly. Set one savepoint before the batch and
either commit all or rollback all:

Savepoint sp = Database.setSavepoint();
try { insert accs; } catch (Exception e) { Database.rollback(sp); }
```

**Detection hint:** Apex with `Database.setSavepoint()` inside a `for` or `while` block.

---

## Anti-Pattern 3: Not nulling IDs after rollback before retry

**What the LLM generates:**

```
try { insert accs; } catch (...) { Database.rollback(sp); }
// later...
insert accs;  // DUPLICATE_VALUE — IDs still populated
```

**Why it happens:** Model forgets rollback doesn't touch in-memory Apex objects.

**Correct pattern:**

```
Database.rollback(sp);
for (Account a : accs) a.Id = null;
// now safe to retry
insert accs;
```

**Detection hint:** Apex retry logic after `Database.rollback` without Id nulling.

---

## Anti-Pattern 4: Rollback outside a catch block

**What the LLM generates:**

```
Savepoint sp = Database.setSavepoint();
insert a;
if (someFlag) Database.rollback(sp);
```

**Why it happens:** Model conflates business-logic rollback with error handling.

**Correct pattern:**

```
Savepoints are for error recovery. If you want conditional business
rollback, don't commit in the first place — gather the records,
decide, THEN insert. Rollback outside catch is usually a design smell
indicating the DML happened too early.
```

**Detection hint:** Apex `Database.rollback(sp)` outside a catch block.

---

## Anti-Pattern 5: Assuming savepoint resets all limits

**What the LLM generates:** After rollback, continues with more SOQL queries expecting the count to reset.

**Why it happens:** Model thinks rollback is total.

**Correct pattern:**

```
Rollback partially resets DML row counts but NOT SOQL query count,
CPU time, or heap. A rollback loop can still blow the 101 SOQL limit.
Design the happy path to stay within limits; don't rely on rollback
to "make room" for retries.
```

**Detection hint:** Retry loops after rollback issuing additional SOQL.
