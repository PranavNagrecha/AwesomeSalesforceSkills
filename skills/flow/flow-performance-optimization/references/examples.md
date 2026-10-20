# Examples — Flow Performance Optimization

## Example 1: Before-Save win

**Context:** After-Save Flow sets `Region__c` based on `BillingCountry`. 200-record batch takes 1.8s due to the second save (illustrative figures; a flow's DML sends the record through the save procedure again, apexdev 264 L15671).

**Fix:** Change entry to Before-Save, which updates the triggering record before it is saved (api_meta 264 L75266-75268). Result: 1.8s → 0.2s (illustrative).

---

## Example 2: Hoisting DML out of a loop

**Context:** Flow updates 200 child Contacts based on Account changes. Loop with Update Records inside = 200 DML statements, past the 150 synchronous limit (apexdev 264 L19757).

**Fix:** Collect Contacts into a collection variable inside the loop; single Update Records outside. Result: 200 DML → 1 DML.

---

## Example 3: Consolidating Get Records

**Context:** Flow calls 4 separate Get Records for Account's Contacts, Opportunities, Cases, Tasks.

**Fix:** Use Account's child relationship Get-Related-Records in a single query. Result: 4 SOQL → 1 SOQL.

---

## Example 4: Asynchronous path offload

**Context:** After-Save Flow does an enrichment callout per record. Save time: 2.5s per record due to vendor latency.

**Fix:** Move the callout to an asynchronous path (`AsyncAfterCommit`, api_meta 264 L74148-74151), which runs after commit (apexdev 264 L15692). Save time drops to 0.3s (illustrative). UNVERIFIED (2026-10-20): the "1-5 min" enrichment delay is not in the corpus.

---

## Example 5: Benchmark-driven PR

Every perf-tuning PR includes the before/after measurement:
```
Before: 200-record update = 3200ms CPU, 15 SOQL, 8 DML
After:  200-record update = 1100ms CPU, 4 SOQL, 2 DML
```

Reviewers can audit the claim.

---

## Anti-Pattern: Micro-optimizing Decisions before fixing SOQL-in-loop

Team spends 2 days reducing Decision branches from 15 to 8; no measurable impact. Meanwhile, the Loop-with-Get-Records was costing 50× more (illustrative). Fix: benchmark first, tune the biggest cost.
