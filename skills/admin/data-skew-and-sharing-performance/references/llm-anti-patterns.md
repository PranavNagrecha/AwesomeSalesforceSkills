# LLM Anti-Patterns — Data Skew and Sharing Performance

Common mistakes AI coding assistants make when generating or advising on Salesforce data skew and sharing recalculation performance.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Recommending ownership redistribution without considering sharing recalculation cost

**What the LLM generates:** "Reassign the 500,000 records from the integration user to individual reps to fix the ownership skew."

**Why it happens:** LLMs identify ownership skew correctly but prescribe mass ownership reassignment as the fix. Reassigning hundreds of thousands of records triggers massive sharing recalculations (implicit shares via role hierarchy, sharing rules). This can lock the org for hours, cause "unable to lock row" errors, and degrade performance for all users.

**Correct pattern:**

```
When fixing ownership skew:
1. Never mass-reassign all records at once.
2. Reassign in small batches (2,000-5,000 records per batch)
   with pauses between batches to let sharing recalculation complete.
3. Schedule reassignment during off-peak hours or a maintenance window.
4. Monitor sharing recalculation status:
   Setup → Sharing Settings → "Defer Sharing Calculations" if available.
5. Consider whether the records actually need individual ownership,
   or if a Queue with sharing rules achieves the access requirement
   without per-record ownership.
```

**Detection hint:** If the output recommends reassigning more than 10,000 records in a single batch without mentioning sharing recalculation impact or batching, the fix may cause an outage. Search for `batch`, `sharing recalculation`, or `off-peak` in the recommendation.

---

## Anti-Pattern 2: Ignoring parent-child skew and focusing only on ownership skew

**What the LLM generates:** "Data skew in Salesforce means one user owns too many records. Redistribute ownership to fix it."

**Why it happens:** LLMs anchor on ownership skew (the most commonly discussed type) and miss parent-child skew. When a single parent record (e.g., one Account) has more than 10,000 child records (Contacts, Cases, Opportunities), operations on those children -- updates, deletes, sharing changes -- cause row lock contention and slow queries.

**Correct pattern:**

```
Two types of data skew:

1. Ownership skew: one user/queue owns > 10,000 records of an object.
   Impact: sharing recalculation slowness, role hierarchy lock contention.

2. Parent-child skew: one parent record has > 10,000 children.
   Impact: record locking during child DML, slow related list loading,
   row lock errors during concurrent child updates.

Diagnosis:
- Run a report on the child object grouped by parent, sorted descending.
- Flag any parent with > 10,000 children.
- For parent-child skew: consider archiving old children, splitting the
  parent into sub-accounts, or using async processing for child updates.
```

**Detection hint:** If the output discusses only ownership skew without mentioning parent-child skew, the diagnosis is incomplete. Search for `parent-child` or `child records` in the analysis.

---

## Anti-Pattern 3: Suggesting Public OWD to eliminate sharing recalculation issues

**What the LLM generates:** "Set the OWD to Public Read/Write to avoid sharing recalculation problems entirely."

**Why it happens:** LLMs see that Private OWD drives sharing recalculation cost and suggest the simplest fix: make everything public. This eliminates sharing recalculation but also eliminates record-level security. Users see all records regardless of ownership or business unit, which violates data governance and compliance requirements.

**Correct pattern:**

```
OWD should be set based on security requirements, not performance:
1. If the business requires record-level data separation → keep Private OWD.
2. Optimize sharing performance with Private OWD:
   - Reduce ownership skew (distribute records across owners).
   - Minimize role hierarchy depth (flatter = less recalculation).
   - Use sharing rules sparingly — each rule adds recalculation cost.
   - Defer sharing calculations during bulk operations.
3. If truly no record-level security is needed → Public Read/Write is valid,
   but document the decision and get business sign-off.
4. Never change OWD to Public solely to fix a performance problem.
```

**Detection hint:** If the output recommends changing OWD to Public as a performance optimization without discussing the security trade-off, the advice is dangerous. Search for `Public Read/Write` combined with `performance` or `fix`.

---

## Anti-Pattern 4: Recommending role hierarchy flattening without analyzing sharing rules

**What the LLM generates:** "Flatten your role hierarchy to reduce sharing recalculation time."

**Why it happens:** LLMs correctly identify that deep role hierarchies increase sharing recalculation cost, but flattening the hierarchy changes which users can see which records via the "Grant Access Using Hierarchies" setting. It also affects sharing rules that reference roles. Flattening without analyzing downstream sharing rule and report visibility impacts creates access regressions.

**Correct pattern:**

```
Before flattening the role hierarchy:
1. Document all sharing rules that reference roles being changed.
2. Identify reports that use "My Team's Records" filtering — these
   depend on the role hierarchy.
3. Check which objects have "Grant Access Using Hierarchies" enabled.
4. Model the proposed hierarchy change in a Full sandbox first.
5. Verify that all users still see the records they need after the change.
6. If flattening is not feasible, reduce skew through ownership
   redistribution or sharing rule consolidation instead.
```

**Detection hint:** If the output recommends flattening the hierarchy without mentioning sharing rule analysis, report impact, or sandbox testing, the recommendation is incomplete. Search for `sharing rule` or `downstream impact` near hierarchy flattening advice.

---

## Anti-Pattern 5: Treating the 10,000 record threshold as a hard system limit

**What the LLM generates:** "Salesforce will fail if one user owns more than 10,000 records."

**Why it happens:** LLMs cite the 10,000 record threshold as a hard limit. It is a guideline, not an enforced cap. The system does not block ownership above 10,000 records. The impact depends on OWD settings, role hierarchy depth, number of sharing rules, and concurrent DML volume. Some orgs have single owners with 100,000+ records and function adequately with Public OWD.

**Correct pattern:**

```
The 10,000 record threshold is a performance guideline, not a hard limit:
- With Private OWD and deep role hierarchy: skew problems may appear
  below 10,000 records if sharing rules are complex.
- With Public OWD: a single owner with 100,000+ records may cause no
  sharing performance issues (but may cause lock contention during bulk DML).
- The actual threshold depends on:
  1. OWD setting (Private amplifies cost).
  2. Role hierarchy depth.
  3. Number and complexity of sharing rules.
  4. Concurrent DML volume on the skewed object.
- Monitor actual performance metrics rather than applying the guideline rigidly.
```

**Detection hint:** If the output states that 10,000 records is a "hard limit" or that the "system will fail" at that threshold, the nuance is missing. Search for `hard limit` or `will fail` near the 10,000 figure.
