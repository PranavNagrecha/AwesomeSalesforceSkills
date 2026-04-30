# LLM Anti-Patterns — Code Coverage Orphan Class Cleanup

Common mistakes AI coding assistants make when generating or advising on orphan-class cleanup.

## Anti-Pattern 1: Generating stub tests to clear the threshold

**What the LLM generates:**

```apex
@isTest
static void coversOldDiscountEngine() {
    new OldDiscountEngine();
}
```

**Why it happens:** Treats coverage as the goal rather than as a downstream signal of real testing.

**Correct pattern:** If the class is unused, delete it. If it is used, write a test that asserts behavior. Stub tests are dishonest.

**Detection hint:** Any test method that contains a `new ClassName()` and no `System.assert` calls.

---

## Anti-Pattern 2: Treating coverage table as authoritative without a fresh run

**What the LLM generates:** "Query `ApexCodeCoverageAggregate WHERE NumLinesCovered = 0` and delete those classes."

**Why it happens:** Treats the persisted snapshot as ground truth.

**Correct pattern:** First run `sf apex run test --test-level RunLocalTests --code-coverage` to refresh the snapshot. Without it, you may delete classes that *would* be covered if tests ran cleanly.

**Detection hint:** A workflow that queries `ApexCodeCoverageAggregate` without a preceding test run.

---

## Anti-Pattern 3: Source-grep on `.cls` only

**What the LLM generates:** `grep -r "OldDiscountEngine" force-app/main/default/classes/`

**Why it happens:** "Apex references live in Apex" intuition.

**Correct pattern:** Apex classes are referenced from `.flow-meta.xml`, `.weblink-meta.xml`, `.flexipage-meta.xml`, `.permissionset-meta.xml`, validation rule formulas (`$Apex.ClassName`), Process Builder XML, custom buttons, and the `CronTrigger` table. Search all of them.

**Detection hint:** A reference search whose include pattern excludes `.flow-meta.xml`, `.flexipage-meta.xml`, or `.weblink-meta.xml`.

---

## Anti-Pattern 4: Recommending delete of `@RestResource` classes

**What the LLM generates:** A destructiveChanges manifest that includes a class because static analysis found "no callers."

**Why it happens:** REST endpoints have no Apex callers — that is the whole point.

**Correct pattern:** Pre-filter the candidate list to exclude any class with HTTP-method annotations.

**Detection hint:** Destructive manifest entry for a class that contains `@RestResource` or any `@Http*` annotation.

---

## Anti-Pattern 5: Counting managed-package code in the orphan list

**What the LLM generates:** A SOQL query that returns managed-package classes (with namespace prefixes) and then proposes "deleting" them.

**Why it happens:** Doesn't know the namespace-prefix exclusion rule.

**Correct pattern:** `WHERE ApexClassOrTrigger.NamespacePrefix = NULL` filters the query to unmanaged code; managed code is not deletable from a subscriber org and does not affect the org-wide threshold.

**Detection hint:** Orphan candidates whose names contain a namespace prefix (e.g., `pkg__OldClass`).
