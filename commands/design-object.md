# /design-object — Design a Setup-ready sObject from a business concept

Wraps [`agents/object-designer/AGENT.md`](../agents/object-designer/AGENT.md). Produces a complete object spec + sfdx metadata scaffold + deployment order.

---

## Step 1 — Collect inputs

Ask the user:

```
1. Business concept (one sentence describing what the object represents)?
   Example: "Track maintenance contracts linked to Accounts, with a primary technician and warranty expiration"

2. Target org alias (required — agent probes for overlapping design)?

3. Expected row volume? small (<100k) / medium (100k-10M) / large (>10M)
   (Default: medium)

4. Integration source (optional)?
   If rows will be sourced from an external system, pass the system name.
   Drives External ID + upsert recommendations.

5. Sensitivity? standard / pii / phi / pci
   (Default: standard; affects encryption + access recommendations)
```

If the concept is under 8 words or lacks enough signal to infer 3+ fields, STOP and ask clarifying questions.

---

## Step 2 — Load the agent

Read `agents/object-designer/AGENT.md` + all mandatory reads.

---

## Step 3 — Execute the plan

Follow the 10-step plan exactly:
1. Probe org for overlapping design
2. Decide standard vs custom
3. Generate API name + label per naming conventions
4. Design the field set
5. Decide record types (only if persona variance signaled)
6. Design sharing posture via the sharing-selection decision tree
7. Plan validation rules at object creation
8. Plan indexes (LDV objects or integration sources)
9. Emit the deployment order
10. Emit the spec + scaffold

---

## Step 4 — Deliver the output

Return the Output Contract:
- Summary + confidence
- Design spec
- Scaffold metadata (fenced XML blocks, one per file)
- Deployment order
- Process Observations
- Citations

---

## Step 5 — Recommend follow-ups

Suggest (but do not auto-invoke):
- `/architect-perms` to design the persona PSes for the new object
- `/audit-validation-rules` after initial VRs are deployed
- `/design-duplicate-rule` if the object is human-identity data
- `/build-flow` for any automation on the new object

---

## What this command does NOT do

- Does not deploy metadata.
- Does not generate permission sets (out of scope — use `/architect-perms`).
- Does not build triggers or flows on the new object.
