# /configure-business-hours — Design or audit Business Hours + Holidays

Wraps [`agents/business-hours-and-holidays-configurator/AGENT.md`](../agents/business-hours-and-holidays-configurator/AGENT.md). Produces region/tier/channel map of calendars, recurring holidays, and the referenced-by inventory (which features key off each calendar).

---

## Step 1 — Collect inputs

Ask the user:

```
1. Target org alias (required — agent probes BusinessHours + Holiday + dependent features)?

2. Regions in scope? (e.g. ["NA", "EMEA", "APAC"])

3. Coverage tiers? (e.g. ["24x7", "standard", "premium"])

4. Channels referencing these hours? (case, chat, entitlement, escalation, approval, email)

5. Recurring holidays to encode? (e.g. "US federal", "UK bank", "IN national")
```

If no regions are named, STOP and ask.

---

## Step 2 — Load the agent

Read `agents/business-hours-and-holidays-configurator/AGENT.md` + mandatory reads (admin/business-hours-and-holidays, admin/escalation-rules, admin/entitlement-management).

---

## Step 3 — Execute the plan

- Probe existing BusinessHours + Holiday.
- Build region × tier × channel matrix.
- Encode holiday set (recurring-rule aware).
- Inventory referenced-by features.
- Flag coverage gaps or orphaned calendars.

---

## Step 4 — Deliver the output

- Summary + confidence
- Calendar matrix
- Holiday list with recurrence
- Referenced-by inventory
- Audit findings (gaps, orphans, timezone drift)
- Process Observations
- Citations

---

## Step 5 — Recommend follow-ups

- `/audit-case-escalation` to verify Escalation Rules reference correct calendars
- `/design-omni-channel` if presence / routing windows depend on these hours
- `/entitlement-milestones` for SLA math linkage

---

## What this command does NOT do

- Does not deploy BusinessHours / Holiday metadata.
- Does not modify dependent features — surfaces them.
