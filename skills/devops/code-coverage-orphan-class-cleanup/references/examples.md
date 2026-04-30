# Examples — Code Coverage Orphan Class Cleanup

## Example 1: Pre-deploy 74.3% rescue

**Context:** Friday deploy returns "Code coverage is 74%. The minimum is 75%." Engineering has the weekend.

**Problem:** Adding 4,000 lines of stub tests is not a real fix and will be reverted next time someone notices.

**Solution:**

```sql
-- Tooling API (Developer Console or sf data query)
SELECT ApexClassOrTrigger.Name, NumLinesCovered, NumLinesUncovered
FROM ApexCodeCoverageAggregate
WHERE NumLinesCovered = 0 AND NumLinesUncovered > 0
ORDER BY NumLinesUncovered DESC
LIMIT 50
```

For each candidate:

```bash
CLASS=OldDiscountEngine
grep -rIn --include='*.cls' --include='*.trigger' --include='*.flow-meta.xml' \
     --include='*.weblink-meta.xml' --include='*.flexipage-meta.xml' \
     "\b${CLASS}\b" force-app/
```

If the grep returns only the class's own definition, and the class is not annotated `@RestResource`, add it to `destructive/destructiveChanges.xml`:

```xml
<types>
    <members>OldDiscountEngine</members>
    <name>ApexClass</name>
</types>
```

Sandbox-deploy the destructive manifest, run RunLocalTests, confirm the test pass rate is unchanged. Then ship to prod.

**Why it works:** Removing 800 lines of 0%-covered code subtracts equally from numerator and denominator's "uncovered" portion — moving the percentage upward without writing any test.

---

## Example 2: Quarterly cleanup with `@deprecated` soft-delete

**Context:** Engineering has a quarterly tech-debt rotation. 30 candidate orphans surfaced.

**Problem:** Some look unused but the grep can't see Apex invoked from Process Builder XML reliably.

**Solution:**

```apex
// Soft-delete pass: annotate then deploy
/**
 * @deprecated Marked 2026-04-30 by tech-debt sweep. Pending delete in 2026-Q3
 * if no usage signal arrives. Owner: platform-eng@.
 */
@deprecated
global class OldDiscountEngine {
    // ... existing code unchanged
}
```

Watch one full release cycle. If Apex Job Logs, Setup Audit Trail, and customer issues stay quiet, schedule the destructive deploy for the following quarter.

**Why it works:** `@deprecated` doesn't change runtime behavior but flags any new compile-time references — engineers will see the warning and surface dependencies the static search missed.

---

## Anti-Pattern: writing 4,000 lines of stub tests to clear the threshold

**What practitioners do:** Generate `Test.startTest(); new ClassName(); Test.stopTest();` blocks for every uncovered class.

**What goes wrong:** Coverage rises but the tests assert nothing. Real bugs pass through. The next deploy is clean for the wrong reason and the team's confidence in tests degrades.

**Correct approach:** Delete the orphans (cheap, real win), or write actual behavior tests for the classes that need to stay (more work, real win). Stub tests are the worst option.
