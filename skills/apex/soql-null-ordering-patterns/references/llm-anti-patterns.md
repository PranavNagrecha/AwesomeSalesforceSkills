# LLM Anti-Patterns — SOQL NULL Ordering Patterns

Common mistakes AI coding assistants make when generating SOQL ORDER BY clauses.

## Anti-Pattern 1: Omitting NULLS clause

**What the LLM generates:**

```soql
SELECT Id FROM Account ORDER BY Last_Activity_Date__c ASC LIMIT 200
```

**Why it happens:** Treats SOQL as PostgreSQL/MySQL-equivalent.

**Correct pattern:**

```soql
SELECT Id FROM Account ORDER BY Last_Activity_Date__c ASC NULLS LAST, Id ASC LIMIT 200
```

**Detection hint:** Any ORDER BY on a non-required field without an explicit `NULLS` clause.

---

## Anti-Pattern 2: No tiebreaker

**What the LLM generates:** Single-field ORDER BY without `Id` (or other unique-field) tiebreaker.

**Why it happens:** Treats single-field ordering as deterministic.

**Correct pattern:** Always end ORDER BY with `Id ASC` (or another guaranteed-unique field). Pagination correctness depends on it.

**Detection hint:** Any ORDER BY clause that doesn't end in `Id ASC` (or similar) when the leading sort field has plausible duplicates.

---

## Anti-Pattern 3: OFFSET-based pagination beyond 2k records

**What the LLM generates:**

```apex
for (Integer page = 0; page < 100; page++) {
    accounts = [... ORDER BY Name LIMIT 200 OFFSET :(page * 200)];
    process(accounts);
}
```

**Why it happens:** OFFSET pagination is universal in other SQL contexts.

**Correct pattern:** Cursor pagination. SOQL OFFSET caps at 2,000 and breaks under concurrent writes anyway.

**Detection hint:** Any `OFFSET` arithmetic above 1,000.

---

## Anti-Pattern 4: Non-keyword null syntax

**What the LLM generates:**

```soql
ORDER BY Last_Activity_Date__c ASC NULLS_LAST
```

**Why it happens:** Underscore form from other dialects.

**Correct pattern:** Two keywords, space-separated: `NULLS LAST`. No underscore, no hyphen.

**Detection hint:** `NULLS_FIRST`, `NULLS_LAST`, `NULLSFIRST`, `NULLSLAST`, or hyphenated variants.

---

## Anti-Pattern 5: Custom-indexed nullable field used as primary sort

**What the LLM generates:** "We've custom-indexed `Last_Sync__c` for filtering and now we'll sort on it for free."

**Why it happens:** Conflates filtering index with sorting index.

**Correct pattern:** Custom indexes on nullable fields don't include nulls by default. High-null-percentage sort fields full-scan unless the index is configured for null inclusion (a Support request). Test with realistic data volumes before relying on the index.

**Detection hint:** Any "this is fast because of the index" claim about a sort over a nullable field.

---

## Anti-Pattern 6: Claiming blanks sort first in a Salesforce list view

**What the LLM generates:** "Blank values sort to the top in ascending order — to find the records missing this field, sort the list view ascending and read from the top."

**Why it happens:** Training data predating Spring '26, when Salesforce "treated blank fields as the lowest value." Models also collapse SOQL and the list-view UI into a single rule, and those two stopped agreeing.

**Correct pattern:** Since Spring '26, list-view sorting treats blanks "as the highest value in the dataset," so an ascending list-view sort *ends* with the blanks. SOQL is unchanged: an ascending SOQL sort still returns nulls first by default. State which surface a null-position claim applies to, and never carry one across the SOQL/list-view boundary.

**Detection hint:** Any "sort ascending to find the empty ones" workflow, or any answer that offers one null-position rule for both SOQL and the list-view UI.
