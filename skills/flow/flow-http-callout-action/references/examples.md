# Examples — Flow HTTP Callout Action

## Example 1: Address verification

**Context:** Lead capture

**Problem:** Previously required Apex for SmartyStreets

**Solution:**

HTTP Callout action with NC to SmartyStreets; map address fields → verified

**Why it works:** Admin-owned integration


---

## Example 2: Weather lookup

**Context:** Field service dispatch

**Problem:** Needed weather at service location

**Solution:**

HTTP Callout to weather.com API; consumed temperature in routing rule

**Why it works:** No Apex overhead

