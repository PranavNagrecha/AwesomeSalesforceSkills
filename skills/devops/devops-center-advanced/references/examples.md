# Examples — DevOps Center Advanced Workflows

## Example 1: Hybrid dev flow

**Context:** Team with admins + devs

**Problem:** Admins needed UI; devs wanted CLI

**Solution:**

Admins use DOC UI; devs branch+commit manually; DOC reconciles via GitHub

**Why it works:** No one blocked on the wrong tool


---

## Example 2: Bypass for P0

**Context:** Prod outage

**Problem:** DOC promotion takes 20 min

**Solution:**

Emergency runbook: direct deploy + post-incident WI reconciliation in DOC

**Why it works:** Minimizes MTTR while preserving audit

