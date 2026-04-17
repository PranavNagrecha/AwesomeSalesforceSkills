# /design-path — Design or audit a Sales/Service Path

Wraps [`agents/path-designer/AGENT.md`](../agents/path-designer/AGENT.md). Produces Key Fields per step, Guidance for Success text (≤ 200 chars), celebration triggers, and the validation-rule harness that gates progression.

---

## Step 1 — Collect inputs

Ask the user:

```
1. Mode? design | audit

2. Target org alias (required — agent probes existing Paths + picklist values)?

3. Object? Opportunity | Lead | Case | Contract | Order | Custom Object

4. Stage picklist API name? (e.g. StageName, Status)

5. Record type (if object uses record types)?

6. Celebration condition (optional)?
   Example: "on close-won when Amount > 500000"
```

If the picklist has fewer than 3 values, STOP — Path is over-engineered for this.

---

## Step 2 — Load the agent

Read `agents/path-designer/AGENT.md` + mandatory reads (admin/path-setup, admin/guidance-for-success, admin/validation-rule-patterns).

---

## Step 3 — Execute the plan

- Enumerate picklist values in picklist sort order.
- For each value: choose Key Fields (3–5) from the record.
- Author Guidance for Success (≤ 200 chars, imperative voice).
- Design VR harness that enforces required-for-stage fields (with bypass Custom Permission).
- Encode celebration trigger if supplied.

---

## Step 4 — Deliver the output

- Summary + confidence
- Per-step table: stage, Key Fields, Guidance for Success
- VR harness (pseudo-XML)
- Celebration config
- Audit findings (stale paths, drift, missing guidance, orphaned VRs)
- Process Observations
- Citations

---

## Step 5 — Recommend follow-ups

- `/design-sales-stages` if Opportunity stage ladder needs redesign before Path
- `/audit-validation-rules` after VRs deploy
- `/architect-perms` for the bypass Custom Permission

---

## What this command does NOT do

- Does not deploy Path metadata.
- Does not edit the underlying picklist — if gaps exist, flags and recommends `/govern-picklists`.
- Does not train reps on the Path UI.
