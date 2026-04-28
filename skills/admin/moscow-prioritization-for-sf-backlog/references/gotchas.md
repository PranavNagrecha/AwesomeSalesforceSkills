# Gotchas — MoSCoW Prioritization for Salesforce Backlog

Non-obvious failure modes that derail prioritization on Salesforce projects.

---

## Gotcha 1: Every Row Tagged Must — No Priority Signal Left

**What happens:** A prioritization session ends with 90% of rows tagged Must. The output looks decisive; it is meaningless. The team has no signal for what to drop when capacity is constrained, so the first slip cascades and the release misses everything.

**When it occurs:** When the session is run as a survey ("does this matter?") rather than a negotiation ("what fails if we don't ship this?"). Common when the sponsor is absent and the BA cannot push back on stakeholders.

**How to avoid:** Enforce the DSDM ~60% rule — Must items account for at most ~60% of total effort in the release. If the tagging exceeds this, stop and re-tag. The skill's checker script flags this.

---

## Gotcha 2: Won't-This-Release vs Won't-Ever Conflated

**What happens:** A row tagged Won't ferments in the backlog for four quarters. Each grooming session, someone asks "why is this still here?" and someone else answers "we said we'd revisit it later". It is never revisited; it is also never archived. It clogs every future grooming.

**When it occurs:** When Won't is treated as a single tag instead of two (Won't-this-release vs Won't-ever). Most tooling does not enforce the sub-tag.

**How to avoid:** Require a `moscow_subtag` of `won't-this-release` or `won't-ever` on every W row. Won't-ever rows must be archived, not left in the active backlog. The checker script enforces this.

---

## Gotcha 3: MoSCoW Without Effort Tier — Capacity Math Is Impossible

**What happens:** Every row is M/S/C/W but no row has an effort tier. The team commits the Must list to a sprint and discovers mid-sprint that Must alone is 60 days of work in a 30-day capacity. Half the Musts slip; stakeholders feel betrayed.

**When it occurs:** When prioritization and estimation are run as separate workshops and the prioritization session ships its output before estimation catches up.

**How to avoid:** Run MoSCoW and effort tagging in the same session, or block the MoSCoW output from being treated as committed until effort is attached. Better an estimate-light prioritization than an estimate-free one.

---

## Gotcha 4: WSJF Without Cost-of-Delay Defined

**What happens:** The team adopts WSJF as a tie-break but never agrees on what "Cost of Delay" means. Each person scores against a different mental model. The numbers diverge wildly; the tie-break produces no consensus.

**When it occurs:** When WSJF is introduced from a SAFe template without the supporting workshop on how to score User-Business Value, Time Criticality, and Risk Reduction / Opportunity Enablement.

**How to avoid:** Before running WSJF, anchor each component with one or two concrete examples ("Time Criticality 13 means 'fail this quarter and we lose the customer'; Time Criticality 1 means 'next year is fine'"). Document the anchors in the team's prioritization charter. Re-anchor every two quarters.

---

## Gotcha 5: Prioritizing Without the Sponsor in the Room

**What happens:** The BA, the dev lead, and a few stakeholders run a prioritization session. The output looks clean. The sponsor reviews it asynchronously a week later, disagrees with three Musts, and the team has to re-do the session with the wasted week sunk.

**When it occurs:** When sponsors are too busy to attend and the team optimizes for "getting it done" over "getting it right". The asynchronous review pattern feels efficient and is not.

**How to avoid:** Treat sponsor presence as a hard precondition. Reschedule the session rather than run it without the budget owner. The output of a sponsor-less session is provisional, not committed.

---

## Gotcha 6: Re-Prioritizing Every Sprint — Death by Churn

**What happens:** Each sprint, stakeholders ask to re-evaluate the backlog and swap Musts in and out. The team spends 20% of its capacity on prioritization meetings instead of building. Throughput collapses; the team blames "too much process" when the real cause is too-frequent process.

**When it occurs:** When the team has not agreed on a grooming cadence, or when the stakeholder culture rewards "always be prioritizing".

**How to avoid:** Pick a cadence (every two sprints is typical) and lock the backlog between groomings. Mid-sprint changes go to the next grooming, not into the current sprint, unless the change is a production-down defect or a regulatory escalation.

---

## Gotcha 7: Regulatory Musts Treated as Immutable

**What happens:** A regulatory item gets tagged Must on day one. Six weeks later, the regulator pushes the deadline by two quarters. Nobody re-tags the item, so it continues to crowd the current release at the expense of higher-value work.

**When it occurs:** When regulatory items are treated as a separate sacred class instead of as backlog rows that follow the same re-grooming rules.

**How to avoid:** At every grooming, re-validate every Must against its rationale. If the regulatory deadline shifted, re-tag accordingly. Musts can move down; they can also move up if scope is added.
