# Examples — API Versioning Strategy

## Example 1: v1 → v2 orders endpoint

**Context:** Rename `customerId` to `accountId`

**Problem:** v1 consumers still rely on customerId

**Solution:**

Keep v1 class intact; publish v2 with new name; both delegate to OrderService.getOrders()

**Why it works:** No consumer is forced to upgrade instantly


---

## Example 2: Sunset instrumentation

**Context:** Before deleting v1

**Problem:** Don't know if anyone still calls it

**Solution:**

Log every v1 call with consumer user id; dashboard shows trend; sunset after 0 calls for 30 days

**Why it works:** Data-driven deprecation

