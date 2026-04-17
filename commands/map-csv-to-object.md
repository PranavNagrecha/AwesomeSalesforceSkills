# /map-csv-to-object — Map a CSV to an sObject for a data load

Wraps [`agents/csv-to-object-mapper/AGENT.md`](../agents/csv-to-object-mapper/AGENT.md). Produces a header→field map, External ID suggestion, transform rules, VR-collision report, and load-plan handoff.

---

## Step 1 — Collect inputs

```
1. CSV headers (paste first row — required)?
2. CSV sample rows (optional, 3–5 lines — helps type-inference)?
3. Target object API name?
4. Target org alias?
5. Load mode?  insert | update | upsert (default: upsert if External ID available)
```

## Step 2 — Load the agent

Read `agents/csv-to-object-mapper/AGENT.md` + mandatory reads, including `templates/admin/naming-conventions.md`.

## Step 3 — Execute the plan

Fetch target object + fields + VRs + duplicate rules, infer type per header, propose field mapping + External ID, design transforms, VR collision check, emit map.

## Step 4 — Deliver the output

Summary, mapping table, External ID recommendation, transform rules, validation collision report, Process Observations, citations. Optionally hand off to `/preflight-load`.

## Step 5 — Recommend follow-ups

- `/preflight-load` to convert the mapping into a go/no-go plan
- `/design-object` if the CSV implies fields that don't yet exist

## What this command does NOT do

- Does not run a data load.
- Does not create missing fields (suggests `/design-object`).
- Does not clean or transform the CSV file itself.
