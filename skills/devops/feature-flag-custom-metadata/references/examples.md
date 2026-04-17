# Examples — Feature Flags via Custom Metadata

## Example 1: Apex accessor

**Context:** New discount engine

**Problem:** Need 10% canary

**Solution:**

`FeatureFlags.isEnabled('NewDiscountEngine')` returns true for users whose hash(UserId)%100 < Percent_Rollout__c

**Why it works:** Deterministic, per-user, no DML


---

## Example 2: LWC toggle via @wire

**Context:** New header variant

**Problem:** Rollout by profile

**Solution:**

@wire(isFeatureEnabled, {name: 'HeaderV2'}) — CMDT checks profile allow-list

**Why it works:** Cacheable wire pulls once per session

