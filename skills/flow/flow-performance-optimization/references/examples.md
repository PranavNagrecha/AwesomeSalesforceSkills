# Examples — Flow Performance Optimization

## Example 1: Before-Save win

**Context:** After-Save Flow sets `Region__c` based on `BillingCountry`. 200-record batch takes 1.8s due to the implicit second DML.

**Fix:** Change entry to Before-Save. Same logic, no extra DML. Result: 1.8s → 0.2s.

---

## Example 2: Hoisting DML out of a loop

**Context:** Flow updates 200 child Contacts based on Account changes. Loop with Update Records inside = 200 DML statements.

**Fix:** Collect Contacts into a collection variable inside the loop; single Update Records outside. Result: 200 DML → 1 DML.

---

## Example 3: Consolidating Get Records

**Context:** Flow calls 4 separate Get Records for Account's Contacts, Opportunities, Cases, Tasks.

**Fix:** Use Account's child relationship Get-Related-Records in a single query. Result: 4 SOQL → 1 SOQL.

---

## Example 4: Scheduled Path offload

**Context:** After-Save Flow does an enrichment callout per record. Save time: 2.5s per record due to vendor latency.

**Fix:** Move the callout to a Scheduled Path +0. Save time drops to 0.3s; enrichment happens async within 1-5 min.

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

Team spends 2 days reducing Decision branches from 15 to 8; no measurable impact. Meanwhile, the Loop-with-Get-Records was costing 50× more. Fix: benchmark first, tune the biggest cost.
