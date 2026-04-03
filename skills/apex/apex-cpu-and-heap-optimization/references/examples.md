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
