# Examples: Duplicate Management

---

## Example: Blocking Contact Duplicates by Email

**Scenario:** Internal users create Contacts manually, and duplicate Contacts with the same business email cause confusion for sales reps.

**Decision:** Use a blocking duplicate rule on Contact with strong email-based matching.

**Why:** The confidence level is high enough that allowing save would create avoidable cleanup work.

---

## Example: Alerting on Account Name + Domain Similarity

**Scenario:** Account names vary slightly (`Acme Inc.`, `Acme Incorporated`, `Acme, Inc.`) and users sometimes add the same company twice.

**Decision:** Use a fuzzy or composite matching approach with steward review rather than hard blocking all saves.

**Why:** Business-account matching often needs human judgment, especially when subsidiaries or regional entities exist.

---

## Example: Merge Governance for Historical Cleanup

**Scenario:** The org already has thousands of duplicate Contacts. The business wants cleanup without losing useful values.

**Approach:**
1. define survivorship rules per field
2. assign a steward queue
3. merge in controlled batches
4. track duplicates found versus duplicates resolved

**Why this works:** It treats merges as governed remediation, not as random record deletion.
