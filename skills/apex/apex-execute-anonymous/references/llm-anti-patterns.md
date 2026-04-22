# LLM Anti-Patterns — Apex Execute Anonymous

Common mistakes AI coding assistants make with anonymous Apex scripts.

## Anti-Pattern 1: No LIMIT on data-fix query

**What the LLM generates:**

```
List<Account> accs = [SELECT Id FROM Account WHERE Rating = null];
for (Account a : accs) a.Rating = 'Warm';
update accs;
```

**Why it happens:** Model writes the intuitive query.

**Correct pattern:**

```
Always bound:

List<Account> accs = [SELECT Id FROM Account WHERE Rating = null LIMIT 200];

Unbounded anonymous loops hit governor limits (10k DML rows per
transaction) mid-stream, partial-commit, and leave the org in a
half-fixed state. Bound the query, iterate, OR use Batch Apex.
```

**Detection hint:** Anonymous script SOQL without `LIMIT` followed by unconditional DML.

---

## Anti-Pattern 2: DML in anonymous with no rollback plan

**What the LLM generates:**

```
update myRecords;
```

**Why it happens:** Model writes the simplest thing that works.

**Correct pattern:**

```
Anonymous auto-commits. Write a dry-run first:

Boolean APPLY = false;
// ... prepare changes
System.debug('Would update ' + records.size());
if (APPLY) update records;

OR use savepoint:

Savepoint sp = Database.setSavepoint();
update records;
System.debug([SELECT ... FROM ... WHERE ...]);  // verify
Database.rollback(sp);  // flip after review

Production data fixes without review = tomorrow's incident.
```

**Detection hint:** Anonymous script with DML and no `Database.setSavepoint` / dry-run toggle.

---

## Anti-Pattern 3: Declaring a method

**What the LLM generates:**

```
void helper(Account a) { /* ... */ }
List<Account> accs = [...];
for (Account a : accs) helper(a);
```

**Why it happens:** Model exports a helper as if it were a full class.

**Correct pattern:**

```
Anonymous has no top-level methods. Inline it:

for (Account a : accs) {
    // inline logic
}

Or declare an inner class:

public class Helper {
    public void process(Account a) { /* ... */ }
}
Helper h = new Helper();
for (Account a : accs) h.process(a);
```

**Detection hint:** Top-level `void` or `public` method declaration in a `.apex` anonymous file.

---

## Anti-Pattern 4: Running against default org for prod fixes

**What the LLM generates:** `sf apex run --file fix.apex` without `--target-org`.

**Why it happens:** Model assumes default org is fine.

**Correct pattern:**

```
sf apex run --target-org prod --file fix.apex

Explicit --target-org prevents the "oh no I was on prod not sandbox"
incident. Make it a checklist item for any anonymous execution
touching DML, and require explicit confirmation (e.g., a shell
prompt) for production.
```

**Detection hint:** CLI docs/runbook referencing `sf apex run` without `--target-org`.

---

## Anti-Pattern 5: Treating anonymous as a test

**What the LLM generates:** Uses `@IsTest` / `testMethod` in an anonymous script.

**Why it happens:** Model thinks anonymous is an alt way to run tests.

**Correct pattern:**

```
Anonymous cannot declare test methods. Test annotations are only
legal inside a test class (file with @IsTest at class level).

To test code: create MyTest.cls with @IsTest methods, run:
    sf apex run test --class-names MyTest --target-org <alias>

Anonymous is for one-off ops, not test automation.
```

**Detection hint:** Anonymous script containing `@IsTest` or `static testMethod`.
