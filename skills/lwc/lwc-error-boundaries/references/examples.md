# Examples — LWC Error Boundaries

## Example 1: Dashboard tile isolation

**Context:** 6-tile sales dashboard

**Problem:** One tile error blanked the page

**Solution:**

Wrap each tile in `<c-error-boundary>`

**Why it works:** Independent widget failures


---

## Example 2: Telemetry wire

**Context:** Need visibility into prod errors

**Problem:** Errors invisible

**Solution:**

errorCallback posts to `@AuraEnabled ErrorLog.record(error, stack)`

**Why it works:** Observability on client failures

