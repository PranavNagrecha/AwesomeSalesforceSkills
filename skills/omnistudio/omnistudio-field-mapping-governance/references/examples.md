# Examples — OmniStudio Field Mapping Governance

## Example 1: CI field check

**Context:** After a field delete

**Problem:** Prod DR silently returned nulls

**Solution:**

CI step parses each DR; cross-refs field existence; fails deploy on missing

**Why it works:** Catches pre-deploy


---

## Example 2: Dead DR cleanup

**Context:** 100 DRs, 12 dead

**Problem:** Clutter + audit risk

**Solution:**

Monthly report of DRs with 0 OmniScript usage; delete after confirmation

**Why it works:** Less surface area

