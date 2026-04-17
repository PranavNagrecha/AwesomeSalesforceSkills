# /design-entitlements — Design or audit Entitlement Processes + Milestones

Wraps [`agents/entitlement-and-milestone-designer/AGENT.md`](../agents/entitlement-and-milestone-designer/AGENT.md). Produces Entitlement Processes, Milestones (with time trigger formulas), Success/Warning/Violation actions, and auto-entitlement rules.

---

## Step 1 — Collect inputs

Ask the user:

```
1. Mode? design | audit

2. Target org alias (required — agent probes Entitlement + Milestone metadata, BusinessHours, Contracts)?

3. SLA terms (for design)?
   - First-response time(s) by priority / channel
   - Resolution time(s) by priority / channel
   - Business-hours calendar(s) to key off

4. Entitlement-to-Account model?
   Options: per-Account | per-Contract | per-Asset | guest / public

5. Case auto-entitlement source? (email-to-case | chat | web-to-case | api)
```

If SLA terms are not specified, STOP.

---

## Step 2 — Load the agent

Read `agents/entitlement-and-milestone-designer/AGENT.md` + mandatory reads (admin/entitlement-management, admin/business-hours-and-holidays, admin/case-escalation-rules).

---

## Step 3 — Execute the plan

- Probe existing Entitlement Processes + Milestones.
- Build Process ladder per priority × channel.
- Encode Milestone time trigger formulas (BusinessHours-aware).
- Define Success / Warning / Violation actions (field updates, task creation, email alerts).
- Design Entitlement Contact model if required.

---

## Step 4 — Deliver the output

- Summary + confidence
- Entitlement Process design
- Milestone table with time trigger formulas
- Actions per milestone
- Auto-entitlement rule logic
- Audit findings (drift, stale processes, missing actions)
- Process Observations
- Citations

---

## Step 5 — Recommend follow-ups

- `/configure-business-hours` if calendars are ambiguous
- `/audit-case-escalation` to verify Escalation Rules align with SLA ladder
- `/design-omni-channel` if routing depends on SLA state

---

## What this command does NOT do

- Does not deploy Entitlement metadata.
- Does not build reports / dashboards for SLA tracking (see `/audit-reports`).
