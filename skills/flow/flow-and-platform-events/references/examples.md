# Examples — Flow and Platform Events

## Example 1: Decouple Opp → Billing

**Context:** Opportunity closed

**Problem:** Previously inline Apex billed synchronously, slow

**Solution:**

Record-triggered flow publishes Opp_Closed__e; PE-triggered flow runs billing async

**Why it works:** Customer-facing save returns fast


---

## Example 2: Fan-out notification

**Context:** Case escalation

**Problem:** 3 subsystems needed notify

**Solution:**

Single PE published; three separate PE-triggered flows each do one job

**Why it works:** Independent failure domains

