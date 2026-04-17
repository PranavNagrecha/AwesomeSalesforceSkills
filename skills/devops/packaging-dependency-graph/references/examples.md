# Examples — Packaging Dependency Graph

## Example 1: Pinned deps

**Context:** 3 packages

**Problem:** service-core broke when sales-core changed

**Solution:**

Pin service-core to sales-core@1.4.0-2

**Why it works:** Explicit coupling caught at CI


---

## Example 2: Fresh-scratch validation

**Context:** Before prod release

**Problem:** Install order bug found only in prod

**Solution:**

CI creates fresh scratch, installs each package in order, runs smoke

**Why it works:** Catches missing deps before go-live

