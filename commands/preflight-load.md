# /preflight-load — Go/no-go checklist for a planned data load

Wraps [`agents/data-loader-pre-flight/AGENT.md`](../agents/data-loader-pre-flight/AGENT.md). Audits the object's active automation, VR bypass state, duplicate rules, required fields, sharing recalc cost, storage quota, and recommends the loader + exact CLI command.

---

## Step 1 — Collect inputs

Ask the user:

```
1. Object API name?
   Example: Account

2. Operation? insert / upsert / update / delete / hard-delete

3. Row count (integer)?
   Example: 800000

4. Target org alias (required — every check is live-org)?

5. Source description (plain English)?
   Example: "NetSuite customer export, one row per account, external-id = netsuite_customer_id__c"

6. External ID field (required for upsert)?

7. Window (optional — business-hours boundary)?
   Example: "this Saturday 2am-6am PT"
```

If the operation is `hard-delete`, require the user to confirm the specific compliance driver.

---

## Step 2 — Load the agent

Read `agents/data-loader-pre-flight/AGENT.md` + mandatory reads.

---

## Step 3 — Execute the plan

1. Probe the object's active automation stack (flows, triggers, VRs, processes)
2. Check each automation for bulk-safety at the target volume
3. Check duplicate rule interactions + policy
4. Check record type defaults for the loader user
5. Check required-field coverage vs source mapping
6. Check sharing recalc cost + data skew
7. Check storage quota impact
8. Pick the loader + emit the exact CLI command
9. Rollback plan

---

## Step 4 — Deliver the output

- Summary: go/no-go + confidence
- Findings table (P0 → P1 → P2)
- Loader recommendation (CLI + batch size + concurrency)
- Pre-load checklist
- Post-load checklist
- Rollback plan
- Process Observations
- Citations

---

## Step 5 — Recommend follow-ups

- `/audit-validation-rules` if VR bypass gaps surfaced
- `/design-duplicate-rule` if dup-rule blocks surfaced
- `/architect-perms` if the integration user's PSG needs work
- `/detect-drift` post-load for verification

---

## What this command does NOT do

- Does not execute the load.
- Does not generate or clean the source CSV.
- Does not deactivate flows, triggers, VRs, or dup rules (recommends what to toggle, user executes).
- Does not deploy any metadata.
