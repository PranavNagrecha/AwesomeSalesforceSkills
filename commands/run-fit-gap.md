# /run-fit-gap — Fit-gap a backlog against a target Salesforce org

Wraps [`agents/fit-gap-analyzer/AGENT.md`](../agents/fit-gap-analyzer/AGENT.md). Classifies every story in a backlog into one of five fit tiers (Standard / Config / Low-Code / Custom / Unfit) using live-org probes, produces a gap inventory across licenses / feature flags / objects / fields / permissions / automation, and surfaces a descope candidate list for the steering committee.

---

## Step 1 — Collect inputs

Ask the user:

```
1. Backlog path (required)?
   Path to a story backlog markdown / JSON envelope (story-drafter output, hand-authored Markdown table, or Jira CSV export).

2. Backlog format?
   story-drafter-json / markdown-table / csv

3. Target org alias (required — the agent refuses without one)?
   The org being fit-gapped (sandbox, full-copy, or production).

4. Release window (optional)?
   Identifier like "R3-2026" used to tag the RTM rows.

5. Assume licenses (optional)?
   Comma-separated list of license SKUs to assume present (used when probing a sandbox missing parent-org licenses).

6. Descope threshold (optional)?
   M / L / XL — Unfit stories at this size or larger are surfaced as descope candidates. Defaults to L.
```

If `target_org_alias` is missing, refuse — fit-gap without an org is guesswork.

---

## Step 2 — Load the agent

Read `agents/fit-gap-analyzer/AGENT.md` + every Mandatory Read in its dependency block.

---

## Step 3 — Execute the plan

Follow the 8-step plan exactly:
1. Probe the org for the canonical inventory (org describe, licenses, objects, automation graph)
2. Parse the backlog into a normalized story list
3. Per-story 5-tier fit classification with confidence + evidence
4. Compile the 6-table gap inventory (licenses, feature flags, objects, fields, permissions, automation)
5. Effort-shape rollup (S/M/L/XL × tier + cross-cloud + NFR-class)
6. Descope candidate list
7. Detect implementation-coupling gaps (e.g. story routes to object-designer but ≥70% similar object exists)
8. Emit RTM-shaped traceability rows

---

## Step 4 — Deliver the output

Return the Output Contract:
- Summary + confidence
- Per-story scorecard
- Gap inventory (6 tables)
- Effort-shape rollup
- Descope candidate list
- Process Observations (4 buckets)
- Citations

---

## Step 5 — Recommend follow-ups

Suggest (but do not auto-invoke):
- `/architect-perms` — for the permission gap rows
- `/design-object` — for net-new object gaps
- `/build-flow` — for declarative automation gaps
- `/audit-record-page`, `/audit-record-types`, `/govern-picklists` — for over-customization signals
- `/audit-sharing` — when sharing-fit gaps are flagged
- `/plan-bulk-migration` — for integration-shaped gaps
- `/author-config-workbook` — once the steering committee commits to the descope/rescope decisions

---

## What this command does NOT do

- Does not deploy gap-fix metadata or order licenses.
- Does not modify the backlog file in place.
- Does not estimate effort in hours.
- Does not make a build-vs-buy recommendation.
- Does not auto-chain to any other command — handoffs are advisory.
- Does not probe orgs other than `target_org_alias`.
