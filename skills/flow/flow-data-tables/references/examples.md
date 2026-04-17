# Examples — Flow Data Tables

## Example 1: Select Contact from list

**Context:** Case creation

**Problem:** Previous custom LWC was overkill

**Solution:**

Get Records → Data Table → single-select → Create Case with selected Contact

**Why it works:** No custom code


---

## Example 2: Multi-select bulk update

**Context:** Update Cases

**Problem:** Needed to pick 5 Cases

**Solution:**

Multi-select Data Table + Loop over selectedRows → Update

**Why it works:** Native UI

