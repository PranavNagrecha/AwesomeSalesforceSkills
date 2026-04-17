# Examples — LWC Virtualized Lists

## Example 1: 10k-row datatable

**Context:** Audit log viewer

**Problem:** Previous render froze browser

**Solution:**

`lightning-datatable enable-infinite-loading onloadmore={next}` returning 200 rows per page

**Why it works:** Native virtual scroll


---

## Example 2: Custom list with IO

**Context:** Activity feed

**Problem:** Non-tabular; needs virtualization

**Solution:**

IntersectionObserver on top/bottom sentinels; maintain visible window + 10 row buffer

**Why it works:** Smooth 60fps on 20k items

