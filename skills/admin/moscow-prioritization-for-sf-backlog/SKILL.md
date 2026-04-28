---
name: moscow-prioritization-for-sf-backlog
description: "Use this skill when prioritizing a Salesforce backlog with the MoSCoW method (Must / Should / Could / Won't) plus an effort + value lens, deciding what fits in the next sprint or release, and using WSJF as a tie-break when MoSCoW alone produces ties. Trigger keywords: MoSCoW prioritization, must should could won't, WSJF salesforce, prioritize salesforce stories, sprint commit, backlog grooming. NOT for story writing or splitting (use admin/user-story-writing-for-salesforce). NOT for release train planning (use agents/release-train-planner). NOT for sizing/estimation method debates — this skill assumes a sizing convention is already in place."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Operational Excellence
  - Reliability
triggers:
  - "how do I MoSCoW prioritize a Salesforce backlog must should could won't"
  - "prioritize salesforce stories must should could when capacity is fixed"
  - "WSJF salesforce tie break when too many stories are tagged Must"
  - "what does Won't mean in MoSCoW for a Salesforce release"
  - "how to commit must-haves to a Salesforce sprint without overcommitting"
  - "MoSCoW backlog grooming for a salesforce admin team"
  - "effort and value tiers for prioritizing a Salesforce backlog"
tags:
  - moscow-prioritization
  - backlog-management
  - wsjf
  - sprint-planning
  - business-analysis
inputs:
  - "Backlog of user stories or work items with story IDs and short descriptions"
  - "Team capacity for the target sprint or release (in story points or person-days)"
  - "Sizing convention already adopted by the team (T-shirt, Fibonacci, person-days)"
  - "Sponsor or product owner availability for the prioritization session"
outputs:
  - "Prioritized backlog table: story_id, moscow, effort, value, wsjf_score, release_target, rationale"
  - "Sprint or release commit list (Must items totalling within capacity)"
  - "Won't list with each row tagged Won't-this-release vs Won't-ever and rationale"
  - "WSJF tie-break worksheet for items where MoSCoW alone produced ties"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-28
---

# MoSCoW Prioritization for Salesforce Backlog

This skill activates when a Salesforce delivery team needs to prioritize a backlog of user stories or change requests for a sprint, release, or roadmap horizon. It produces a fixed-shape prioritized backlog: each row carries a MoSCoW tag, an effort tier, a value tier, an optional WSJF tie-break score, a release target, and a one-line rationale. The output is the canonical handoff into the release-train-planner, the orchestrator, and the deployment-risk-scorer agents.

---

## Before Starting

Gather this context before running a prioritization session:

- **Is the sponsor or product owner in the room?** MoSCoW is a negotiated taxonomy, not a survey. If the person who owns the budget or the business outcome is not present, the output is provisional and must be reviewed before commit.
- **Is the sizing convention agreed?** This skill assumes the team has already adopted a sizing convention (T-shirt S/M/L/XL, Fibonacci, or person-days). If sizing is contested, stop and resolve that first — MoSCoW without a shared effort signal is theatre.
- **Is the team capacity known and stable?** Capacity must be expressed in the same unit as effort tiers (e.g., person-days remaining in the sprint after meetings, leave, support rotation). The Must commit is bounded by capacity, not by enthusiasm.
- **Is each backlog item written as a Salesforce-ready user story?** If stories are vague ("improve case management"), prioritization is meaningless. Refer to `admin/user-story-writing-for-salesforce` and finish that first.

---

## Core Concepts

### The MoSCoW Rubric

MoSCoW comes from DSDM/Agile Project Framework and forces every backlog item into one of four named buckets. The discipline of the method is in the definitions — not in the act of labelling.

- **Must have (M)** — The release fails its objective if this item is not delivered. "Must" is reserved for items that are non-negotiable: a regulator requires it, a contractual deadline depends on it, the org will not function without it. The DSDM canon recommends that **Must items account for no more than ~60% of total effort** in a release; if Musts exceed this, the release is overcommitted and at risk.
- **Should have (S)** — Important and high-value, but not release-breaking. The release ships even if a Should slips, though stakeholders will be unhappy. Should items are the natural overflow when capacity is tight.
- **Could have (C)** — Nice to have. Delivered only if Musts and Shoulds finish ahead of capacity. Most "polish", reporting refinements, and minor UX upgrades land here. Could items are the buffer that absorbs estimate misses.
- **Won't have (W)** — Explicitly out of scope. Critical: Won't comes in two flavours that must never be conflated.
  - **Won't this release** — agreed-out for the current horizon, but a candidate for a future release. Goes back to the backlog tagged for re-grooming.
  - **Won't ever** — agreed-out permanently. Document the rationale (regulatory, architectural, strategic). Archive the item — do not let it ferment in the backlog.

The most common MoSCoW failure mode is everything-is-Must. If the backlog has more than ~60% Must by effort, the rubric has degraded into a wishlist and the prioritization session has not actually happened.

### The Effort + Value Lens

MoSCoW alone is a coarse signal. Pair every item with two orthogonal scales so the team can sort within a bucket and detect cheap wins:

- **Effort tier (S/M/L/XL):**
  - **S** — half a day or less (a field, a list view, a permission set tweak)
  - **M** — one to three days (a record-triggered flow, a small report bundle, a validation rule pack)
  - **L** — three to ten days (a multi-object flow, a Lightning page redesign, an Apex trigger refactor)
  - **XL** — more than ten days (a new object model, an integration, a Lightning component suite). XL items in a sprint are a smell — split.
- **Value tier (1–5):** business value as judged by the sponsor.
  - **5** — strategic; tied to a board-level OKR or a regulatory deadline
  - **4** — high; closes a meaningful pain point or unlocks revenue
  - **3** — solid; clear ROI but not strategic
  - **2** — incremental; small productivity gain
  - **1** — cosmetic; gold-plating

The (effort, value) pair is the crucial second signal. A "Must, XL, value 2" row is almost certainly miscategorized and should be challenged.

### WSJF as the Tie-Break

When MoSCoW + effort + value still produce ties — typically a cluster of "Must, M, value 4" items competing for the same sprint slot — escalate to WSJF (Weighted Shortest Job First) from SAFe:

```
WSJF = Cost of Delay / Job Size
Cost of Delay = User-Business Value + Time Criticality + Risk Reduction / Opportunity Enablement
```

Each component is scored on the modified Fibonacci 1, 2, 3, 5, 8, 13. Job Size uses the same scale (or the team's existing effort points). Sort descending: highest WSJF wins the slot.

WSJF is a tie-break, not a replacement for MoSCoW. Do not rank the entire backlog by WSJF — the cognitive cost is high and the comparative scoring degrades quickly past 15–20 items.

### The Release Commit Rule

Once items are tagged, commit them to a release or sprint with this rule:

- **Sum of Must effort ≤ team capacity for the horizon**
- **Sum of Must + Should effort ≤ ~80% of capacity** (leaves slack for estimate misses and unplanned support)
- **Could items fill any remaining slack** but are explicitly stretch goals, not commitments

If Must alone exceeds capacity, the prioritization is invalid: either capacity must be raised (more people, longer horizon) or items must be re-tagged. The stalemate is the signal — do not paper over it by promising and missing.

---

## Common Patterns

### Pattern: Capacity-Bounded Sprint Commit

**When to use:** Two-week sprints with a stable team.

**How it works:**
1. Compute capacity: (team size × sprint days) − (leave + support rotation + ceremonies). Express in the team's effort unit.
2. Tag every backlog candidate M/S/C/W with rationale.
3. Attach effort tier and value tier to every M and S item (W and C items can be effort-tagged later).
4. Sum Must effort. If > capacity, escalate to the sponsor: cut, defer, or raise capacity.
5. Sum Must + Should effort. Cap at ~80% of capacity. The remainder is the Could stretch zone.
6. Record `release_target` for every committed row; set Won't-this-release rows to the next horizon and Won't-ever rows to `archived`.

**Why not just the top-N stories:** Top-N ignores effort. Six "value 5, XL" items overcommit a sprint that easily holds twelve "value 4, S" items.

### Pattern: WSJF Tie-Break Workshop

**When to use:** When MoSCoW labelling produces a cluster of indistinguishable Musts that exceed sprint capacity.

**How it works:**
1. Pull only the tied cluster into a worksheet (typically 5–15 rows).
2. For each row, score: User-Business Value (1–13), Time Criticality (1–13), Risk Reduction / Opportunity Enablement (1–13), Job Size (1–13).
3. Compute WSJF = (UBV + TC + RR/OE) / JS.
4. Sort descending. The top items take the available slots; the rest become Should-have for the next horizon.
5. Persist the score in the row's `wsjf_score` column so the rationale is auditable.

**Why not skip WSJF and just argue:** Argument scales badly past three people. WSJF gives the team a shared rubric; the score is the artefact, not the verdict.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Backlog has >60% Must by effort | Stop and re-tag — the rubric has collapsed | Everything-is-Must means nothing is prioritized |
| Item is regulatory or contractually due this release | Must, value 5, with effort tier | Regulatory deadlines are non-negotiable but still need sizing |
| Sponsor cannot decide between two Musts of equal effort | Run WSJF on just the tied pair | Tie-break with a shared rubric beats arguing |
| Item has been Won't for three releases running | Reclassify Won't-ever and archive | Stale Won't items pollute backlog grooming sessions |
| Effort estimate is XL | Split the story before prioritizing | XL items hide complexity; they distort capacity math |
| Item is "nice UX polish" | Could, value 1–2 | Polish is the buffer, not the commitment |
| Stakeholder wants Should re-tagged as Must mid-sprint | Reject — process churn is the larger cost | Re-prioritizing every sprint destroys throughput |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner activating this skill:

1. **Ingest the backlog** — load every candidate as a row; verify each row has a story_id and a description sufficient to judge value and effort. Reject rows that are not real user stories.
2. **Tag MoSCoW** — assign M / S / C / W to every row with a one-line rationale. Won't rows must be sub-tagged Won't-this-release vs Won't-ever.
3. **Attach effort tier** — assign S / M / L / XL to every M and S row. Flag XL items for splitting before they are committed.
4. **Attach value tier** — assign 1–5 to every M and S row, validated with the sponsor.
5. **WSJF tie-break** — for any cluster of Musts that exceeds sprint capacity, score Cost of Delay / Job Size and persist `wsjf_score`.
6. **Commit Must to the current sprint or release** — verify Sum(Must effort) ≤ capacity and Sum(Must+Should) ≤ ~80% of capacity. Set `release_target` for every committed row.
7. **Re-prioritize at backlog grooming** — refresh tags only at the agreed grooming cadence (typically every two sprints). Avoid mid-sprint churn.

---

## Handoff Schema

Every prioritized backlog row produced by this skill MUST conform to this JSON shape so downstream agents (release-train-planner, orchestrator, deployment-risk-scorer) can consume it:

```json
{
  "story_id": "STORY-1234",
  "moscow": "M",
  "moscow_subtag": null,
  "effort": "M",
  "value": 4,
  "wsjf_score": null,
  "release_target": "2026-Spring",
  "rationale": "Regulator requires audit trail by end of FY26 Q3."
}
```

- `moscow` — one of `M | S | C | W`
- `moscow_subtag` — null for M/S/C; for W must be `won't-this-release` or `won't-ever`
- `effort` — one of `S | M | L | XL`
- `value` — integer 1–5
- `wsjf_score` — number, populated only when WSJF tie-break was used; otherwise null
- `release_target` — ISO-style release identifier or `backlog` (Won't-this-release) or `archived` (Won't-ever)
- `rationale` — one sentence; required for every W row, recommended for every M row

The canonical table form lives in `templates/moscow-prioritization-for-sf-backlog-template.md`.

---

## Review Checklist

Run through these before handing the prioritized backlog to delivery:

- [ ] Every row has a MoSCoW tag (M/S/C/W) — no nulls
- [ ] Every Won't row has a sub-tag (Won't-this-release vs Won't-ever) and a rationale
- [ ] Every Must and Should row has effort and value tiers
- [ ] Sum of Must effort ≤ team capacity for the target horizon
- [ ] Sum of Must + Should effort ≤ ~80% of capacity
- [ ] Must items account for ≤ ~60% of backlog effort
- [ ] No XL items in the sprint commit (split first)
- [ ] WSJF was applied wherever Musts tied at the capacity boundary
- [ ] Sponsor or product owner signed off in the prioritization session
- [ ] Won't-ever rows have been archived, not left in the active backlog

---

## Salesforce-Specific Gotchas

Non-obvious behaviours that cause real prioritization failures on Salesforce projects:

1. **Regulatory Musts that aren't actually Must** — "Compliance wants it" is not the same as "the regulator will fine us if we don't ship by date X". Force a citation: which regulation, which clause, which deadline. Otherwise it goes Should.
2. **Won't-this-release ferments into Won't-ever silently** — A row tagged Won't-this-release for four consecutive grooming cycles is no longer being deferred; it is being declined. Surface it for a real archive decision.
3. **Capacity inflated by counting full FTEs** — A two-week sprint with five admins ≠ 50 admin-days. Subtract leave, support rotation, ceremonies, code review, and UAT participation. Real capacity is typically 50–60% of nominal.
4. **MoSCoW without effort hides infeasibility** — A backlog of 80 Musts feels confident until the team realizes Must alone is 200 days of work for a 40-day sprint. Always pair MoSCoW with effort.
5. **Mid-sprint re-prioritization** — Stakeholders frequently ask to swap a Must in once a sprint starts. The cost of churn (context switching, partial work abandoned, retests) is almost always higher than the cost of waiting one sprint.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Prioritized backlog table | One row per story with story_id, moscow, effort, value, wsjf_score, release_target, rationale |
| Sprint or release commit list | The Must subset whose effort sum is within team capacity |
| Won't list (split) | Won't-this-release rows (return to backlog) vs Won't-ever rows (archived) with rationale |
| WSJF tie-break worksheet | For tied Must clusters: UBV, Time Criticality, RR/OE, Job Size, computed WSJF |

---

## Related Skills

- `admin/user-story-writing-for-salesforce` — author the stories before prioritizing them
- `admin/requirements-gathering-for-sf` — finish discovery before tagging MoSCoW
- `agents/release-train-planner/AGENT.md` — consumes the prioritized backlog to plan releases
- `agents/orchestrator/AGENT.md` — uses the release_target and effort signal to schedule which agents run when
