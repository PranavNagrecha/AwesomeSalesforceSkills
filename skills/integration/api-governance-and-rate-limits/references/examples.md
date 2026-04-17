# Examples — API Governance and Rate Limits

## Example 1: Throttle heavy ETL

**Context:** ETL hit 95% at 3am

**Problem:** Blocks other integrations

**Solution:**

Move ETL to Bulk API 2.0; reduces REST calls 1000x

**Why it works:** Different allocation bucket; bulk is designed for scale


---

## Example 2: Composite for UI

**Context:** LWC needed 5 parallel fetches

**Problem:** 5 API calls per page load

**Solution:**

One Composite request

**Why it works:** Reduces allocation burn per user

