# Examples — OmniStudio Cache Strategies

## Example 1: Product catalog IP

**Context:** Hundreds of shoppers

**Problem:** IP ran 50k times/hr

**Solution:**

Cache 15 min TTL → 95% hit ratio

**Why it works:** Huge back-end relief


---

## Example 2: Bust on update

**Context:** Admin edits reference data

**Problem:** Cache served stale for 60 min

**Solution:**

AfterUpdate trigger publishes event; subscriber busts partition

**Why it works:** Immediate freshness

