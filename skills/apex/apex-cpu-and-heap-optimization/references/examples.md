# Examples — Apex CPU And Heap Optimization

## Example 1: Replace Nested Loops With A Map

**Context:** A service compares Opportunities to a list of related Quotes and hits CPU time issues under volume.

**Problem:** The code loops over every Opportunity and every Quote, creating a quadratic comparison pattern.

**Solution:**

```apex
Map<Id, List<Quote>> quotesByOpportunityId = new Map<Id, List<Quote>>();
for (Quote quoteRecord : quotes) {
    if (!quotesByOpportunityId.containsKey(quoteRecord.OpportunityId)) {
        quotesByOpportunityId.put(quoteRecord.OpportunityId, new List<Quote>());
    }
    quotesByOpportunityId.get(quoteRecord.OpportunityId).add(quoteRecord);
}

for (Opportunity opp : opportunities) {
    List<Quote> matchingQuotes = quotesByOpportunityId.get(opp.Id);
    if (matchingQuotes == null) {
        continue;
    }
    // process only the relevant quotes
}
```

**Why it works:** A map lookup replaces repeated full-list scanning, reducing CPU cost dramatically.

---

## Example 2: Lightweight CPU Checkpoints During Diagnosis

**Context:** A trigger handler has several suspect blocks and no clear hotspot.

**Problem:** Refactoring blindly wastes time and can miss the real bottleneck.

**Solution:**

```apex
Integer cpuBefore = Limits.getCpuTime();
processEligibilityRules(records);
System.debug(LoggingLevel.INFO, 'CPU eligibility=' + (Limits.getCpuTime() - cpuBefore));

cpuBefore = Limits.getCpuTime();
applyTransformations(records);
System.debug(LoggingLevel.INFO, 'CPU transform=' + (Limits.getCpuTime() - cpuBefore));
```

**Why it works:** Temporary checkpoints identify the high-cost block before deeper refactoring.

---

## Anti-Pattern: Serializing Huge Payloads For Debugging

**What practitioners do:** They call `JSON.serializePretty(largeList)` or build giant debug strings to inspect state.

**What goes wrong:** Heap usage spikes and the diagnostics contribute to the failure.

**Correct approach:** Log identifiers, counts, or targeted samples instead of entire payloads.

```apex
// Instead of JSON.serializePretty(orders) — which allocates a second full copy
// of the payload on the heap — log the shape and one representative id.
ApplicationLogger.info(
    'OrderSyncService.apply',
    'orders=' + orders.size()
        + ' firstId=' + (orders.isEmpty() ? 'none' : String.valueOf(orders[0].Id))
        + ' heapBytes=' + Limits.getHeapSize() + ' of ' + Limits.getLimitHeapSize()
);
```

---

## Example 3: Reading The Limit Usage Block Out Of A Debug Log

**Context:** A nightly job fails intermittently and nobody can say which ceiling it hit.

**Problem:** The exception text names one limit, but the transaction was near several.

**Solution:** Pull the last log for the run and read the cumulative block the platform writes at the end of the transaction.

```bash
sf apex get log --number 1 --target-org prodRO | sed -n '/CUMULATIVE_LIMIT_USAGE/,/CUMULATIVE_LIMIT_USAGE_END/p'
```

That prints one `LIMIT_USAGE_FOR_NS` section per namespace, in the form documented at `apexdev.txt` L38275–L38284:

```text
LIMIT_USAGE_FOR_NS|(default)|
  Number of SOQL queries: 0 out of 100
  Number of DML statements: 0 out of 150
  Maximum CPU time: 0 out of 10000
  Maximum heap size: 0 out of 6000000
```

**Why it works:** It gives every ceiling for the failing transaction at once, per namespace, so you learn whether your own code or a packaged namespace was the consumer. Two reading rules: `Maximum heap size: 0` means the platform declined to measure a small transaction rather than that no heap was used (`apexdev.txt` L38239–L38241), and CPU and heap are shared across namespaces even when SOQL and DML are not (`salesforce_app_limits_cheatsheet.txt` L241–L248), so a small number under `(default)` does not clear your code.
