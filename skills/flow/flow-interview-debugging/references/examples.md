# Examples — Flow Interview Debugging

## Example 1: Central error log

**Context:** 12 flows, scattered errors

**Problem:** Team missed 3 prod incidents

**Solution:**

Fault connector on every DML → Create Log__c with `{$Flow.FaultMessage}`, flow name, record id; Slack alert on count>5/hr

**Why it works:** Visibility + proactive SLA


---

## Example 2: Debug 'field not writable'

**Context:** Screen save failure

**Problem:** Error text unhelpful

**Solution:**

Run flow with Debug; inspect field/value on the Update element; discover Field-Level Security issue

**Why it works:** FLS is invisible otherwise

