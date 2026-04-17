# /design-assignment-rules — Design or audit Assignment + Auto-Response rules

Wraps [`agents/assignment-and-auto-response-rules-designer/AGENT.md`](../agents/assignment-and-auto-response-rules-designer/AGENT.md). Produces the rule-entry table, queue design, email-template mapping, and cutover plan.

---

## Step 1 — Collect inputs

Ask the user:

```
1. Mode? design | audit

2. Target org alias (required — agent probes queues, templates, and existing rules)?

3. Object? Lead | Case

4. Routing dimensions?
   Any of: source, geography, product, tier, language, custom predicate

5. Auto-response scope? (yes | no — default yes for Web-to-Lead / Email-to-Case)

6. Coexistence with existing routing? (Flow | Lead Routing Rules | Omni-Channel | none)
```

If dimensions are unspecified, STOP and ask for the routing matrix.

---

## Step 2 — Load the agent

Read `agents/assignment-and-auto-response-rules-designer/AGENT.md` + mandatory reads (admin/lead-routing, admin/case-routing, admin/queues-and-groups, admin/email-templates).

---

## Step 3 — Execute the plan

- Probe queues, groups, email templates, existing rules.
- Build the routing matrix.
- Author the rule-entry table (order matters — first match wins).
- Map auto-response templates per rule entry.
- Emit cutover plan that coexists with existing routing.

---

## Step 4 — Deliver the output

- Summary + confidence
- Rule-entry table (ordered)
- Queue / group design
- Email-template mapping
- Cutover plan
- Audit findings (audit mode)
- Process Observations
- Citations

---

## Step 5 — Recommend follow-ups

- `/design-lead-routing` if Lead Routing Rules replace part of this
- `/design-omni-channel` for Chat/Messaging routing overlap
- `/architect-perms` for queue-membership permission design
- `/modernize-email-templates` if auto-response templates are stale

---

## What this command does NOT do

- Does not deploy rules.
- Does not create queues — recommends their shape.
- Does not manage holiday / business-hours calendars (use `/configure-business-hours`).
